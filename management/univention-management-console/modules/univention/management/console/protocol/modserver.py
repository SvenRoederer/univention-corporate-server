#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module server process implementation
#
# Copyright (C) 2006, 2007 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from server import *
from message import *
from definitions import *

import univention.management.console.acl as umc_acl

import univention.debug as ud

import locale
import notifier
import notifier.threads as threads

class ModuleServer( Server ):
	def __init__( self, socket, module, interface, timeout = 300,
				  check_acls = True ):
		Server.__init__( self, ssl = False, unix = socket, magic = False )
		self.signal_connect( 'session_new', self._client )
		self.__name = module
		self.__module = module
		self.__comm = None
		self.__client = None
		self.__buffer = ''
		self.__acls = None
		self.__timeout = timeout * 1000
		self.__timer = notifier.timer_add( self.__timeout, self._timed_out )
		self.__partial_timer = None
		self.__active_requests = 0
		self.__check_acls = check_acls
		self.__interface = interface
		self.__queue = ''
		self.__username = None
		self.__password = None
		self._load_module()

	def _load_module( self ):
		try:
			modname = self.__module
			self.__module = None
			for type in ( 'handlers', 'wizards' ):
				try:
					file = 'univention.management.console.%s.%s' % ( type, modname )
					self.__module = __import__( file, [], [], modname )
				except:
					pass
			if not self.__module:
				raise Exception( "Module '%s' could not be found. Exiting ..." )
			self.__handler = self.__module.handler()
			self.__handler.set_interface( self.__interface )
			self.__commands = self.__module.command_description
			self.__handler.signal_connect( 'success', notifier.Callback( self._reply, True ) )
			self.__handler.signal_connect( 'failure', notifier.Callback( self._reply, True ) )
			self.__handler.signal_connect( 'partial', notifier.Callback( self._reply, False ) )
		except Exception, e:
			import traceback
			traceback.print_exc()
			sys.exit( 1 )

	def _reply( self, msg, final ):
		if final:
			self.__active_requests -= 1
		self.response( msg )
		if not self.__active_requests:
			self.__timer = notifier.timer_add( self.__timeout, self._timed_out )

	def _timed_out( self ):
		self.exit()
		sys.exit( 0 )

	def _client( self, client, socket ):
		self.__comm = socket
		self.__client = client
		notifier.socket_add( self.__comm, self._recv )

	def _recv( self, socket ):
		if self.__timer:
			notifier.timer_remove( self.__timer )

		data = socket.recv( 16384 )

		# connection closed?
		if not len( data ):
			socket.close()
			# remove socket from notifier
			return False

		self.__buffer += data

		msg = None
		try:
			while self.__buffer:
				msg = Message()
				self.__buffer = msg.parse( self.__buffer )
				self.handle( msg )
		except IncompleteMessageError, e:
			pass
		except ( ParseError, UnknownCommandError ), e:
			res = Response( msg )
			res.id( -1 )
			res.status( e.args[ 0 ] )
			self.response( res )

		return True

	def handle( self, msg ):
		if msg.command == 'SET':
			resp = Response( msg )
			resp.status( 200 )
			if 'commands/permitted' in msg.arguments:
				self.__acls = umc_acl.ACLs( acls = msg.options[ 'acls' ] )
				self.__handler.set_acls( self.__acls )
			elif 'username' in msg.arguments:
				self.__username = msg.options[ 'username' ]
				self.__handler.set_username( self.__username )
			elif 'credentials' in msg.arguments:
				self.__username = msg.options[ 'username' ]
				self.__password = msg.options[ 'password' ]
				self.__handler.set_username( self.__username )
				self.__handler.set_password( self.__password )
			elif 'locale' in msg.arguments:
				self.__locale = msg.options[ 'locale' ]
				try:
					locale.setlocale( locale.LC_MESSAGES,
									 locale.normalize( self.__locale ) )
				except locale.Error:
					ud.debug( ud.ADMIN, ud.WARN, "modserver.py: specified locale is not available (%s)" % self.__locale )
					# specified locale is not available
					resp.status( 601 )
			else:
				resp = None
			if resp:
				self.response( resp )
			return

		if msg.arguments:
			cmd = msg.arguments[ 0 ]
			if self.__commands.has_key( cmd ) and \
				   ( not self.__check_acls or \
					 self.__acls.is_command_allowed( cmd, options = msg.options ) ):
				descr = self.__commands[ cmd ]
				# TODO: partial response
# 				cb = notifier.Callback( self.__partial_response, msg )
# 				self.__partial_timer = notifier.timer_add( 600, cb )
				self.__handler.execute( descr.method, msg )
				self.__active_requests += 1
				return
			else:
				resp = Response( msg )
				if not self.__commands.has_key( cmd ):
					resp.status( 401 ) # unknown command
					resp.report = status_information( 401 )
				else:
					resp.status( 415 ) # command not allowed
					resp.report = status_information( 415 )
				self.response( resp )

		if not self.__active_requests:
			self.__timer = notifier.timer_add( self.__timeout, self._timed_out )

	# TODO: partial response
# 	def __partial_response( self, msg ):
# 		resp = Response( msg )
# 		resp.status( 210 )
# 		ud.debug( ud.ADMIN, ud.INFO, "PARTIAL RESPONSE: %s" % msg )
# 		self.response( resp )
# 		return True

	def _do_send( self, socket ):
		length = len( self.__queue )
		ret = self.__comm.send( self.__queue )
		if ret < length:
			self.__queue = self.__queue[ ret : ]
			return True
		else:
			self.__queue = ''
			return False


	def response( self, msg ):
		if msg.isFinal() and self.__partial_timer:
			ud.debug( ud.ADMIN, ud.INFO, "KILL PARTIAL RESPONSE TIMER: %s" % self.__partial_timer )
			notifier.timer_remove( self.__partial_timer )
			self.__partial_timer = None
		data = str( msg )
		length = len( data )
		ret = self.__comm.send( data )
		if ret < length:
			if not self.__queue:
				notifier.socket_add( self.__comm, self._do_send, notifier.IO_WRITE )
			self.__queue += data[ ret : ]
