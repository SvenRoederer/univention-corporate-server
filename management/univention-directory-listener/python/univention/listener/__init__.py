#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2017-2024 Univention GmbH
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
# you and Univention.
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
Listener module API

To create a listener module (LM) with this API, create a Python file in
:file:`/usr/lib/univention-directory-listener/system/` which includes:

1. a subclass of :py:class:`ListenerModuleHandler`
2. with an inner class `Configuration` that has at least the class attributes `name`, `description` and `ldap_filter`

See :file:`/usr/share/doc/univention-directory-listener/examples/` for examples.
"""


from .api_adapter import ListenerModuleAdapter
from .exceptions import ListenerModuleConfigurationError, ListenerModuleRuntimeError
from .handler import ListenerModuleHandler
from .handler_configuration import ListenerModuleConfiguration


__all__ = [
    'ListenerModuleAdapter',
    'ListenerModuleConfiguration',
    'ListenerModuleConfigurationError',
    'ListenerModuleHandler',
    'ListenerModuleRuntimeError',
]
