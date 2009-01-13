#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manage ad connector
#
# Copyright (C) 2009 Univention GmbH
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

import univention.management.console as umc
import univention.management.console.categories as umcc
import univention.management.console.protocol as umcp
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud

import univention.config_registry

import notifier.popen
import os, stat, shutil

import subprocess, time

FN_BINDPWD = '/etc/univention/connector/ad/bindpwd'
DIR_WEB_AD = '/var/www/univention-ad-connector'

_ = umc.Translation('univention.management.console.handlers.adconnector').translate

icon = 'adconnector/module'
short_description = _('AD Connector')
long_description = _('Configure AD Connector')
categories = ['all', 'system']


command_description = {
	'adconnector/overview': umch.command(
		short_description = _('Overview'),
		long_description = _('Overview'),
		method = 'overview',
		values = { },
		startup = True,
		priority = 100,
		caching = False
	),
	'adconnector/configure': umch.command(
		short_description = _('Configure AD Connector'),
		long_description = _('Configure AD Connector'),
		method = 'configure',
		values = {
			'action': umc.String( _('action') ),
			'ad_ldap_host': umc.String( _('Hostname of Active Directory server'), regex = '^([a-z]([a-z0-9-]*[a-z0-9])*[.])+[a-z]([a-z0-9-]*[a-z0-9])*$' ),
			'ad_ldap_base': umc.String( _('BaseDN of Active Directory') ),
			'ad_ldap_binddn': umc.String( _('DN of replication user') ),
			'ad_ldap_bindpw': umc.String( _('Password of replication user') ),
			'ad_poll_sleep': umc.String( _('Poll Interval (seconds)'), regex = '^[0-9]+$' ),
			'ad_windows_version': umc.String( _('Version of Windows server') ),
			'ad_retry_rejected': umc.String( _('Retry interval for rejected objects'), regex = '^[0-9]+$' ),
			'debug_level': umc.String( _('Debug level') ),
			'debug_functions': umc.String( _('Debug functions') ),
			},
		caching = False
	),
}


import inspect
def debugmsg( component, level, msg ):
	info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
	printInfo=[]
	if len(info[0])>25:
		printInfo.append('...'+info[0][-22:])
	else:
		printInfo.append(info[0])
	printInfo.extend(info[1:3])
	ud.debug(component, level, "%s:%s: %s" % (printInfo[0], printInfo[1], msg))


class handler(umch.simpleHandler):

	def __init__(self):
		_d = ud.function('adconnector.handler.__init__')

		umch.simpleHandler.__init__(self, command_description)

		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()
		self.status_configured = False
		self.status_certificate = False
		self.status_running = False
		self.guessed_baseDN = None
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }

		self.__update_status()



	def overview(self, obj):
		_d = ud.function('adconnector.handler.overview')
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }
		self.finished(obj.id(), None)



	def configure(self, obj):
		_d = ud.function('adconnector.handler.configure')
		debugmsg( ud.ADMIN, ud.INFO, 'configure: options=%s' % obj.options )

		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }
		self.guessed_baseDN = None

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 1' )

		if obj.options.get('action','') == 'save':
			# if action == "save" then save values to UCR

			try:
				fn = '%s/.htaccess' % DIR_WEB_AD
				fd = open( fn, 'w' )
				fd.write('require user %s\n' % self._username)
				fd.close()
				os.chmod( fn, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH )
				os.chown( fn, 0, 0 )
			except Exception, e:
				self.msg['error'].append( _('An error occured while saving .htaccess (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
				debugmsg( ud.ADMIN, ud.ERROR, 'An error occured while saving .htaccess (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )

			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 10' )

			for umckey, ucrkey in ( ( 'ad_ldap_host', 'connector/ad/ldap/host' ),
									( 'ad_ldap_base', 'connector/ad/ldap/base' ),
									( 'ad_ldap_binddn', 'connector/ad/ldap/binddn' ),
									( 'ad_poll_sleep', 'connector/ad/poll/sleep' ),
									):
				if obj.options.get( umckey ):
					debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: umckey=%s' % umckey )
					univention.config_registry.handler_set( [ u'%s=%s' % (ucrkey, obj.options.get(umckey)) ] )

			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 11' )

			if obj.options.get('ad_ldap_bindpw'):
				fn = self.configRegistry.get('connector/ad/ldap/bindpwd', FN_BINDPWD)
				try:
					fd = open( fn ,'w')
					fd.write( obj.options.get('ad_ldap_bindpw') )
					fd.close()
					os.chmod( fn, stat.S_IRUSR | stat.S_IWUSR )
					os.chown( fn, 0, 0 )
				except Exception, e:
					self.msg['error'].append( _('saving bind password failed (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
					debugmsg( ud.ADMIN, ud.ERROR, 'saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )
				univention.config_registry.handler_set( [ u'connector/ad/ldap/bindpw=%s' % FN_BINDPWD ] )

			self.msg['hint'].append( _('AD connector settings have been saved.') )
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 22' )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 23' )

		if obj.options.get('action','') == 'save':

			if os.path.exists( '/etc/univention/ssl/%s' % obj.options.get('ad_ldap_host') ):
				self._copy_certificate( obj )
				self.finished(obj.id(), None)
			else:
				cmd = 'univention-certificate new -name "%s"' % obj.options.get('ad_ldap_host')
				debugmsg( ud.ADMIN, ud.INFO, 'creating new SSL certificate: %s' % cmd )
				proc = notifier.popen.Shell( cmd, stdout = True )
				cb = notifier.Callback( self._configure_create_cert_return, obj )
				proc.signal_connect( 'finished', cb )
				proc.start()

		elif obj.options.get('action','') == 'guess_basedn' and obj.options.get('ad_ldap_host'):

			# if FQDN has been set and ldap_base is unknown then call ldapsearch to determine ldap_base
			cmd = 'ldapsearch -x -s base -b "" namingContexts -LLL -h "%s"' % obj.options.get('ad_ldap_host')
			debugmsg( ud.ADMIN, ud.INFO, 'determine baseDN of specified system: %s' % cmd )
			proc = notifier.popen.Shell( cmd, stdout = True )
			cb = notifier.Callback( self._configure_guess_basedn_return, obj )
			proc.signal_connect( 'finished', cb )
			proc.start()

		else:
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 3' )
			self.finished(obj.id(), None)

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 4' )


	def _copy_certificate(self, obj, error_if_missing = False):
		ssldir = '/etc/univention/ssl/%s' % obj.options.get('ad_ldap_host')
		if os.path.exists( ssldir ):
			for fn in ( 'private.key', 'cert.pem' ):
				try:
					shutil.copy2( '%s/%s' % (ssldir, fn), '%s/%s' % (DIR_WEB_AD, fn) )
				except Exception, e:
					self.msg['error'].append( _('copy of %s/%s to %s/%s failed (exception=%s)') % (ssldir, fn, DIR_WEB_AD, fn, str(e.__class__)) )
					debugmsg( ud.ADMIN, ud.ERROR, 'copy of %s/%s to %s/%s failed (exception=%s)' % (ssldir, fn, DIR_WEB_AD, fn, str(e.__class__)) )
		else:
			if error_if_missing:
				self.msg['error'].append( _('creation of certificate failed (%s)') % ssldir )
				debugmsg( ud.ADMIN, ud.ERROR, 'creation of certificate failed (%s)' % ssldir )


	def _configure_create_cert_return( self, pid, status, buffer, obj ):
		_d = ud.function('adconnector.handler._configure_create_cert_return')
		self._copy_certificate( obj, error_if_missing=True )
		self.finished(obj.id(), None)


	def _configure_guess_basedn_return( self, pid, status, buffer, obj ):
		_d = ud.function('adconnector.handler._configure_guess_basedn_return')
		# dn:
		# namingContexts: DC=ad,DC=univention,DC=de
		# namingContexts: CN=Configuration,DC=ad,DC=univention,DC=de
		# namingContexts: CN=Schema,CN=Configuration,DC=ad,DC=univention,DC=de
		# namingContexts: DC=DomainDnsZones,DC=ad,DC=univention,DC=de
		# namingContexts: DC=ForestDnsZones,DC=ad,DC=univention,DC=de

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 10' )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: buffer=%s' % buffer )
		self.guessed_baseDN = None
		for line in buffer:
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: line="%s"' % line )
			if line.startswith('namingContexts: '):
				debugmsg( ud.ADMIN, ud.INFO, line )
				dn = line.split(': ',1)[1].strip()
				if self.guessed_baseDN == None or len(dn) < len(self.guessed_baseDN):
					self.guessed_baseDN = dn

		if self.guessed_baseDN == None:
			self.msg['warn'].append( _('Could not determine baseDN of given ldap server. Maybe FQDN is wrong or unresolvable!') )
			debugmsg( ud.ADMIN, ud.ERROR, 'Could not determine baseDN of given ldap server. Maybe FQDN is wrong or unresolvable! FQDN=%s' % obj.options.get('ad_ldap_host') )

		debugmsg( ud.ADMIN, ud.INFO, 'guessed baseDN: %s' % self.guessed_baseDN )

		self.finished(obj.id(), None)


	#######################
	# The revamp functions
	#######################


	def bool2yesno(self, val):
		if val:
			return _('yes')
		return _('no')


	def __get_request(self, cmd, title):
		req = umcp.Command(args=[ cmd ])

		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', title)

		return req


	def __update_status(self):
		self.configRegistry.load()
		self.status_configured = (  self.configRegistry.get('connector/ad/ldap/host') and \
									self.configRegistry.get('connector/ad/ldap/base') and \
									self.configRegistry.get('connector/ad/ldap/binddn') and \
									self.configRegistry.get('connector/ad/ldap/bindpw')
									)
		self.status_certificate = False
		self.status_running = self.__is_process_running('python.* /usr/sbin/univention-ad-connector')


	def __is_process_running(self, command):
		p1 = subprocess.Popen(['ps -ef | egrep "%s" | grep -v grep' % command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		p1.communicate()
		return (p1.returncode == 0)   # p1.returncode is 0 if process is running


	# This revamp function shows the Overview site
	def _web_overview(self, obj, res):
		_d = ud.function('adconnector.handler._web_overview')

		self.__update_status()

		#### AD Connector Status Frame
		list_status = umcd.List()

		list_status.add_row( [ umcd.Text( _('Configured:') ), umcd.Text( self.bool2yesno( self.status_configured ) ) ] )
		list_status.add_row( [ umcd.Text( _('AD certificate installed:') ), umcd.Text( self.bool2yesno( self.status_certificate ) ) ] )
		list_status.add_row( [ umcd.Text( _('Running:') ), umcd.Text( self.bool2yesno( self.status_running ) ) ] )

		frame_status = umcd.Frame( [list_status], _('AD connector status'))


		#### AD Connector Actions Frame
		list_actions = umcd.List()


		btn_configure = umcd.Button(_('Configure AD connector'), 'actions/configure',
									actions = [ umcd.Action( self.__get_request( 'adconnector/configure', _('Configure AD Connector') ) ) ] )
		list_actions.add_row( [ btn_configure ] )


		img = umcd.Link( description = _('IMG'),                                       link='/univention-ad-connector/', icon=icon )
		btn = umcd.Link( description = _('Download .msi package and UCS certificate'), link='/univention-ad-connector/' )
		list_actions.add_row( [ (img,btn) ] )


		btn_upload_cert = umcd.Button(_('Upload AD certificate'), 'actions/configure',
									 actions = [ umcd.Action( self.__get_request( 'adconnector/uploadcert', _('Upload AD certificate') ) ) ] )
		list_actions.add_row( [ btn_upload_cert ] )


		if self.status_running:
			title = _('Stop AD connector')
		else:
			title = _('Start AD connector')
		btn_startstop = umcd.Button( title, 'actions/configure',
									actions = [ umcd.Action( self.__get_request( 'adconnector/startstop', title ) ) ] )
		list_actions.add_row( [ btn_startstop ] )


		frame_actions = umcd.Frame( [list_actions], _('Actions'))


		res.dialog = [frame_status, frame_actions]

		self.revamped(obj.id(), res)


	# This revamp function shows the Overview site
	def _web_configure(self, obj, res):
		_d = ud.function('adconnector.handler._web_configure')
		debugmsg( ud.ADMIN, ud.INFO, 'web_configure: options=%s' % obj.options )

		self.__update_status()

		list_items = umcd.List()
		list_id = []

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 20' )

		# ask for ldap_host
		if obj.options.get('action','') == 'guess_basedn':
			ldaphost = obj.options.get('ad_ldap_host')
		else:
			ldaphost = self.configRegistry.get('connector/ad/ldap/host', '')
		inp_ldap_host = umcd.make( self['adconnector/configure']['ad_ldap_host'], default = ldaphost )
		list_items.add_row( [ inp_ldap_host ] )
		list_id.append( inp_ldap_host.id() )

		# create guess basedn button
		opts = { 'action': 'guess_basedn' }
		req = umcp.Command( args = [ 'adconnector/configure' ], opts = opts )
		actions = ( umcd.Action( req, [ inp_ldap_host.id() ] ), )
		btn_guess = umcd.Button( _('Determine BaseDN'), 'actions/ok', actions = actions, close_dialog = False )

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 21' )

		# ask for ldap_base and/or display a first guess based on ldapsearch call
		if obj.options.get('action','') == 'guess_basedn' and self.guessed_baseDN:
			basedn = self.guessed_baseDN
		else:
			basedn = self.configRegistry.get('connector/ad/ldap/base', '')
		inp_ldap_base = umcd.make( self['adconnector/configure']['ad_ldap_base'], default = basedn )
		list_items.add_row( [ inp_ldap_base, btn_guess ] )
		list_id.append( inp_ldap_base.id() )

		# ask for ldap_binddn and/or display a first guess based on ldapsearch call
		if obj.options.get('action','') == 'guess_basedn' and self.guessed_baseDN:
			binddn = 'cn=Administrator,cn=users,%s' % basedn
		else:
			binddn = self.configRegistry.get('connector/ad/ldap/binddn', '')
		inp_ldap_binddn = umcd.make( self['adconnector/configure']['ad_ldap_binddn'], default = binddn )
		list_items.add_row( [ inp_ldap_binddn ] )
		list_id.append( inp_ldap_binddn.id() )

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 22' )

		# get bind password if UCR variable is already set and file exists
		pwd = ''
		fn = self.configRegistry.get('connector/ad/ldap/bindpwd', FN_BINDPWD)
		if os.path.exists( fn ):
			try:
				pwd = open( fn, 'r' ).read().strip('\n')
			except Exception, e:
				self.msg['error'].append( _('reading bind password failed (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
				debugmsg( ud.ADMIN, ud.ERROR, 'reading bind password failed (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )

		# ask for ldap_bindpwd
		inp_ldap_bindpwd = umcd.make( self['adconnector/configure']['ad_ldap_bindpw'], default = pwd )
		list_items.add_row( [ inp_ldap_bindpwd ] )
		list_id.append( inp_ldap_bindpwd.id() )

		# ask for poll_sleep
		inp_poll_sleep = umcd.make( self['adconnector/configure']['ad_poll_sleep'], default = self.configRegistry.get('connector/ad/poll/sleep', '5') )
		list_items.add_row( [ inp_poll_sleep ] )
		list_id.append( inp_poll_sleep.id() )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 23' )

		opts = { 'action': 'save' }
		req = umcp.Command( args = [ 'adconnector/configure' ], opts = opts )
		actions = ( umcd.Action( req, list_id ), )
		btn_set = umcd.Button( _('Save Changes'), 'actions/ok', actions = actions, close_dialog = False )
		list_items.add_row( [ btn_set ] )

		frame = umcd.Frame( [list_items], _('AD Connector Configuration'))

		res.dialog = []
		if self.msg['error'] or self.msg['warn'] or self.msg['hint']:
			lst = umcd.List()
			for key in ( 'error', 'warn', 'hint' ):
				for msg in self.msg[key]:
					lst.add_row( [ msg ] )
			res.dialog.append( umcd.Frame( [lst] ) )

		res.dialog.append(frame)

		self.revamped(obj.id(), res)




