# -*- coding: utf-8 -*-
#
# Univention Management Console
#  next generation of UMC modules
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

"""
.. _sec-module-definitions:

Module definitions
==================

The UMC server does not load the Python modules to get the details about
the modules name, description and functionality. Therefore each UMC
module must provide an XML file containing this kind of information.

The following example defines a module with the id `udm`:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <umc version="2.0">
        <module id="udm" icon="udm-module" version="1.0">
            <name>Univention Directory Manager</name>
            <description>Manages all UDM modules</description>
            <flavor icon="udm-users" id="users/user">
                <name>Users</name>
                <description>Managing users</description>
            </flavor>
            <categories>
                <category name="domain" />
            </categories>
            <requiredCommands>
                <requiredCommand name="udm/query" />
            </requiredCommands>
            <command name="udm/query" function="query" />
            <command name="udm/containers" function="containers" />
        </module>
    </umc>

The *module* tag defines the basic details of a UMC module

id
    This identifier must be unique among the modules of an UMC server. Other
    files may extend the definition of a module by adding more flavors
    or categories.

icon
    The value of this attribute defines an identifier for the icon that
    should be used for the module. Details for installing icons can be
    found in the section :ref:`chapter-packaging`

The child elements *name* and *description* define the English human
readable name and description of the module. For other translations the
build tools will create translation files. Details can be found in the
section :ref:`chapter-packaging`.

This example defines a so called flavor. A flavor defines a new name,
description and icon for the same UMC module. This can be used to show
several"virtual" modules in the overview of the web frontend. Additionally the flavor is passed to the UMC server with each request i.e. the UMC module has the possibility to act differently for a specific flavor.

As the next element *categories* is defined in the example. The child
elements *category* set the categories wthin the overview where the
module should be shown. Each module can be more than one category. The
attribute name is to identify the category internally. The UMC server
brings a set of pre-defined categories:

favorites
    This category is intended to be filled by the user herself.

system
    Tools manipulating the system itself (e.g. software installation)
    should go in here.

At the end of the definition file a list of commands is specified. The
UMC server only passes commands to a UMC module that are defined. A
command definition has two attributes:

name
    is the name of the command that is passed to the UMC module. Within
    the request this is the path segement of the URL after /univention/command/.

function
    defines the method to be invoked within the Python module when the
    command is called.

keywords
    defined keywords for the module to ensure searchability

The translations are stored in extra po files that are generated by the
UMC build tools.
"""

import copy
import os
import re
import sys
import xml.etree.cElementTree as ET  # noqa: S405
import xml.parsers.expat

from .config import ucr
from .log import RESOURCES
from .tools import JSON_List, JSON_Object


KEYWORD_PATTERN = re.compile(r'\s*,\s*')


class Command(JSON_Object):
    """Represents a request URL path handled by a module"""

    SEPARATOR = '/'

    def __init__(self, name='', method=None, allow_anonymous=False):
        self.name = name
        if method:
            self.method = method
        else:
            self.method = self.name.replace(Command.SEPARATOR, '_')
        self.allow_anonymous = allow_anonymous

    def fromJSON(self, json):
        for attr in ('name', 'method'):
            setattr(self, attr, json[attr])
        self.allow_anonymous = json.get("allow_anonymous", False)


class Flavor(JSON_Object):
    """
    Defines a flavor of a module. This provides another name and icon
    in the overview and may influence the behavior of the module.
    """

    def __init__(self, id='', icon='', name='', description='', overwrites=None, deactivated=False, priority=-1, translationId=None, keywords=None, categories=None, required_commands=None, version=None, hidden=False):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.overwrites = overwrites or []
        self.keywords = keywords or []
        self.deactivated = deactivated
        self.priority = priority
        self.translationId = translationId
        self.categories = categories or []
        self.required_commands = required_commands or []
        self.version = version
        self.hidden = hidden

    def merge(self, other):
        self.id = self.id or other.id
        self.version = self.version or other.version
        self.name = self.name or other.name
        self.description = self.description or other.description
        self.icon = self.icon or other.icon
        self.overwrites = list(set(self.overwrites + other.overwrites))
        self.keywords = list(set(self.keywords + other.keywords))
        self.deactivated = self.deactivated or other.deactivated
        self.priority = self.priority or other.priority
        self.translationId = self.translationId or other.translationId
        self.categories = list(set(self.categories + other.categories))
        self.required_commands = list(set(self.required_commands + other.required_commands))
        self.hidden = self.hidden or other.hidden

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.json())


class Module(JSON_Object):
    """Represents a command attribute"""

    def __init__(self, id='', name='', url='', description='', icon='', categories=None, flavors=None, commands=None, priority=-1, keywords=None, translationId=None, required_commands=None, version=None, singleton=False, proxy=None):
        self.id = id
        self.name = name
        self.url = url
        self.description = description
        self.keywords = keywords or []
        self.icon = icon
        self.priority = priority
        self.flavors = JSON_List()
        self.translationId = translationId
        self.required_commands = required_commands or []
        self.version = version
        self.singleton = singleton
        self.proxy = proxy
        if flavors is not None:
            self.append_flavors(flavors)

        if categories is None:
            self.categories = JSON_List()
        else:
            self.categories = categories
        if commands is None:
            self.commands = JSON_List()
        else:
            self.commands = commands

    def fromJSON(self, json):
        if isinstance(json, dict):
            for attr in ('id', 'name', 'description', 'icon', 'categories', 'keywords', 'singleton', 'proxy'):
                setattr(self, attr, json[attr])
            commands = json['commands']
        else:
            commands = json
        for cmd in commands:
            command = Command()
            command.fromJSON(cmd)
            self.commands.append(command)

    def append_flavors(self, flavors):
        for flavor in flavors:
            # remove duplicated flavors
            if flavor.id not in [iflavor.id for iflavor in self.flavors] or flavor.deactivated:
                self.flavors.append(flavor)
            else:
                RESOURCES.warn('Duplicated flavor for module %s: %s' % (self.id, flavor.id))

    def merge_flavors(self, other_flavors):
        for other_flavor in other_flavors:
            try:  # merge other_flavor into self_flavor
                self_flavor = [iflavor for iflavor in self.flavors if iflavor.id == other_flavor.id][0]  # noqa: RUF015
                self_flavor.merge(other_flavor)
            except IndexError:  # add if other_flavor does not exist
                RESOURCES.debug('Add flavor: %s' % other_flavor.name)
                self.flavors.append(other_flavor)

    def merge(self, other):
        """merge another Module object into current one"""
        if not self.name:
            self.name = other.name

        if not self.icon:
            self.icon = other.icon

        if not self.description:
            self.description = other.description

        self.version = self.version or other.version
        self.singleton = self.singleton or other.singleton
        self.proxy = self.proxy or other.proxy
        self.keywords = list(set(self.keywords + other.keywords))
        self.merge_flavors(other.flavors)
        self.categories = JSON_List(set(self.categories + other.categories))
        self.commands = JSON_List(set(self.commands + other.commands))
        self.required_commands = JSON_List(set(self.required_commands + other.required_commands))

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.json())


class Link(Module):
    pass


class XML_Definition(ET.ElementTree):
    """container for the interface description of a module"""

    def __init__(self, root=None, filename=None):
        ET.ElementTree.__init__(self, element=root, file=filename)
        self.root = self.getroot()

    @property
    def name(self):
        return self.findtext('name')

    @property
    def version(self):
        return self.root.findtext('version')

    @property
    def url(self):
        return self.findtext('url')

    @property
    def description(self):
        return self.findtext('description')

    @property
    def keywords(self):
        return KEYWORD_PATTERN.split(self.findtext('keywords', '')) + [self.name]

    @property
    def id(self):
        return self.root.get('id')

    @property
    def priority(self):
        try:
            return float(self.root.get('priority', -1))
        except ValueError:
            RESOURCES.warn('No valid number type for property "priority": %s' % self.root.get('priority'))
        return None

    @property
    def translationId(self):
        return self.root.get('translationId', '')

    @property
    def singleton(self):
        return self.root.get('singleton', 'no').lower() in ('yes', 'true', '1')

    @property
    def icon(self):
        return self.root.get('icon')

    @property
    def deactivated(self):
        return self.root.get('deactivated', 'no').lower() in ('yes', 'true', '1')

    @property
    def flavors(self):
        """Retrieve list of flavor objects"""
        for elem in self.findall('flavor'):
            name = elem.findtext('name')
            priority = None
            try:
                priority = float(elem.get('priority', -1))
            except ValueError:
                RESOURCES.warn('No valid number type for property "priority": %s' % elem.get('priority'))
            categories = [cat.get('name') for cat in elem.findall('categories/category')]
            # a empty <categories/> causes the module to be hidden! while a not existing <category> element causes that the categories from the module are used
            hidden = elem.find('categories') is not None and not categories
            yield Flavor(
                id=elem.get('id'),
                icon=elem.get('icon'),
                name=name,
                overwrites=elem.get('overwrites', '').split(','),
                deactivated=(elem.get('deactivated', 'no').lower() in ('yes', 'true', '1')),
                translationId=self.translationId,
                description=elem.findtext('description'),
                keywords=re.split(KEYWORD_PATTERN, elem.findtext('keywords', '')) + [name],
                priority=priority,
                categories=categories,
                required_commands=[cmd.get('name') for cmd in elem.findall('requiredCommands/requiredCommand')],
                version=self.version,
                hidden=hidden,
            )

    @property
    def categories(self):
        return [elem.get('name') for elem in self.findall('categories/category')]

    def commands(self):
        """Generator to iterate over the commands"""
        for command in self.findall('command'):
            yield command.get('name')

    def get_module(self):
        cls = {
            'link': Link,
            'module': Module,
        }.get(self.root.tag, Module)
        return cls(
            self.id, self.name, self.url, self.description, self.icon, self.categories, self.flavors,
            priority=self.priority,
            keywords=self.keywords,
            translationId=self.translationId,
            required_commands=[cat.get('name') for cat in self.findall('requiredCommands/requiredCommand')],
            version=self.version,
            singleton=self.singleton,
            proxy=self.root.get('proxy'),
        )

    def get_flavor(self, name):
        """Retrieves details of a flavor"""
        for flavor in self.flavors:
            if flavor.name == name:
                return flavor

    def get_command(self, name):
        """Retrieves details of a command"""
        for command in self.findall('command'):
            cname = command.get('name')
            if not cname:
                continue
            pattern = re.compile('^%s$' % (cname if command.get('pattern', '0').lower() in ('yes', 'true', '1') else re.escape(cname)))
            if pattern.match(name):
                return Command(name, command.get('function'), command.get('allow_anonymous', '0').lower() in ('yes', 'true', '1'))

    def __bool__(self):
        module = self.find('module')
        return module is not None and len(module) != 0
    __nonzero__ = __bool__

    def __repr__(self):
        return '<XML_Definition %s (%r)>' % (self.id, self.name)


_manager = None


class Manager(dict):
    """Manager of all available modules"""

    DIRECTORY = os.path.join(sys.prefix, 'share/univention-management-console/modules')

    def __init__(self):
        dict.__init__(self)

    def modules(self):
        """Returns list of module names"""
        return list(self.keys())

    def load(self):
        """
        Loads the list of available modules. As the list is cleared
        before, the method can also be used for reloading
        """
        RESOURCES.info('Loading modules ...')
        modules = {}
        for filename in os.listdir(Manager.DIRECTORY):
            if not filename.endswith('.xml'):
                continue
            try:
                parsed_xml = ET.parse(os.path.join(Manager.DIRECTORY, filename))  # noqa: S313
                RESOURCES.debug('Loaded module %s' % filename)
                for mod_tree in parsed_xml.getroot():
                    mod = XML_Definition(root=mod_tree)
                    if mod.deactivated:
                        RESOURCES.info('Module is deactivated: %s' % filename)
                        continue
                    # save list of definitions
                    modules.setdefault(mod.id, []).append(mod)
            except (xml.parsers.expat.ExpatError, ET.ParseError) as exc:
                RESOURCES.warn('Failed to load module %s: %s' % (filename, exc))
                continue
        self.clear()
        self.update(modules)

    def is_command_allowed(self, acls, command, hostname=None, options={}, flavor=None):
        for module_xmls in self.values():
            for module_xml in module_xmls:
                cmd = module_xml.get_command(command)
                if cmd and cmd.allow_anonymous:
                    return True
        return acls.is_command_allowed(command, hostname, options, flavor)

    def get_module(self, module_id):
        # get first Module and merge all subsequent Module objects into it
        mod = None
        for module_xml in self[module_id]:
            nextmod = module_xml.get_module()
            if mod:
                mod.merge(nextmod)
            else:
                mod = nextmod
        return mod

    def permitted_commands(self, hostname, acls):
        """
        Retrieves a list of all modules and commands available
        according to the ACLs (instance of LDAP_ACLs)

        { id : Module, ... }
        """
        RESOURCES.info('Retrieving list of permitted commands')
        modules = {}
        for module_id in self:
            mod = self.get_module(module_id)

            if ucr.is_true('umc/module/%s/disabled' % (module_id)):
                RESOURCES.info('module %s is deactivated by UCR' % (module_id))
                continue

            if isinstance(mod, Link):
                if mod.url:
                    modules[module_id] = mod
                else:
                    RESOURCES.info('invalid link %s: no url element' % (module_id))
                continue

            if not mod.flavors:
                flavors = [Flavor(id=None, required_commands=mod.required_commands)]
            else:
                flavors = copy.copy(mod.flavors)

            deactivated_flavors = set()
            for flavor in flavors:
                if ucr.is_true('umc/module/%s/%s/disabled' % (module_id, flavor.id)):
                    RESOURCES.info('flavor %s (module=%s) is deactivated by UCR' % (flavor.id, module_id))
                    # flavor is deactivated by UCR variable
                    flavor.deactivated = True

                RESOURCES.debug('mod=%r flavor=%r deactivated=%r hidden=%r' % (module_id, flavor.id, flavor.deactivated, flavor.hidden))
                if flavor.deactivated:
                    deactivated_flavors.add(flavor.id)
                    continue

                required_commands = [module_xml.get_command(command) for module_xml in self[module_id] for command in module_xml.commands() if command in flavor.required_commands]
                apply_function = all
                if not required_commands:
                    # backwards compatibility. if any of the commands defined in the module is allowed this module is visible
                    apply_function = any
                    required_commands = [module_xml.get_command(command) for module_xml in self[module_id] for command in module_xml.commands()]

                if apply_function(cmd.allow_anonymous or acls.is_command_allowed(cmd.name, hostname, flavor=flavor.id) for cmd in required_commands):
                    modules.setdefault(module_id, mod)
                    all_commands = {module_xml.get_command(command) for module_xml in self[module_id] for command in module_xml.commands()}
                    modules[module_id].commands = JSON_List(set(modules[module_id].commands) | all_commands)
                elif mod.flavors:
                    # if there is not one command allowed with this flavor
                    # it should not be shown in the overview
                    mod.flavors.remove(flavor)

            mod.flavors = JSON_List(f for f in mod.flavors if f.id not in deactivated_flavors)

            overwrites = set()
            for flavor in mod.flavors:
                overwrites.update(flavor.overwrites)

            mod.flavors = JSON_List(f for f in mod.flavors if f.id not in overwrites)

        return modules

    def is_singleton(self, module_name):
        return self[module_name] and self.get_module(module_name).singleton

    def proxy_address(self, module_name):
        return self[module_name] and self.get_module(module_name).proxy

    def module_providing(self, modules, command):
        """
        Searches a dictionary of modules (as returned by
        permitted_commands) for the given command. If found, the id of
        the module is returned, otherwise None
        """
        RESOURCES.info('Searching for module providing command %s' % command)
        for module_id in modules:
            for cmd in modules[module_id].commands:
                if cmd.name == command:
                    RESOURCES.info('Found module %s' % module_id)
                    return module_id

        RESOURCES.info('No module provides %s' % command)
        return None


if __name__ == '__main__':
    mgr = Manager()
