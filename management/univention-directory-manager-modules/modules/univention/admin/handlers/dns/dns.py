# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

"""|UDM| module for all |DNS| objects"""

from typing import TYPE_CHECKING

import six

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.dns.alias
import univention.admin.handlers.dns.forward_zone
import univention.admin.handlers.dns.host_record
import univention.admin.handlers.dns.ns_record
import univention.admin.handlers.dns.ptr_record
import univention.admin.handlers.dns.reverse_zone
import univention.admin.handlers.dns.srv_record
import univention.admin.handlers.dns.txt_record
import univention.admin.localization
from univention.admin.layout import Tab


if TYPE_CHECKING:
    import univention.admin
    import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.dns')
_ = translation.translate


module = 'dns/dns'

childs = False
short_description = _('All DNS zones')
object_name = _('DNS zone')
object_name_plural = _('DNS zones')
long_description = _('Manage the Domain Name System.')
operations = ['search']
childmodules = ['dns/forward_zone', 'dns/reverse_zone']
virtual = True
options = {}  # type: dict[str, univention.admin.option]
property_descriptions = {
    'name': univention.admin.property(
        short_description=_('Name'),
        long_description='',
        syntax=univention.admin.syntax.dnsName,
        include_in_default_search=True,
        required=True,
        identifies=True,
    ),
}
layout = [Tab(_('General'), _('Basic settings'), layout=["name"])]
mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module


def rewrite(filter_s, **args):
    # type: (str, str) -> str
    if not filter_s:
        return filter_s
    filter_p = univention.admin.filter.parse(filter_s)
    mapping = univention.admin.mapping.mapping()
    for key, value in args.items():
        mapping.register(key, value)
    univention.admin.filter.walk(filter_p, univention.admin.mapping.mapRewrite, arg=mapping)
    return six.text_type(filter_p)


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
    # type: (None, univention.admin.uldap.access, str, str, univention.admin.handlers.simpleLdap | None, str, bool, bool, int, int) -> list[univention.admin.handlers.simpleLdap]
    ptr_filter = rewrite(filter_s, name='address')
    fw_zone_filter = rewrite(filter_s, name='zone')
    rv_zone_filter = rewrite(filter_s, name='subnet')
    ret = []  # type: list[univention.admin.handlers.simpleLdap]
    if superordinate:
        if superordinate.module == "dns/forward_zone":
            ret += univention.admin.handlers.dns.host_record.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
            ret += univention.admin.handlers.dns.alias.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
            ret += univention.admin.handlers.dns.srv_record.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
            ret += univention.admin.handlers.dns.txt_record.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
        else:
            ret += univention.admin.handlers.dns.ptr_record.lookup(co, lo, ptr_filter, base, superordinate, scope, unique, required, timeout, sizelimit)
        ret += univention.admin.handlers.dns.ns_record.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    else:
        ret += univention.admin.handlers.dns.forward_zone.lookup(co, lo, fw_zone_filter, base, superordinate, scope, unique, required, timeout, sizelimit)
        ret += univention.admin.handlers.dns.reverse_zone.lookup(co, lo, rv_zone_filter, base, superordinate, scope, unique, required, timeout, sizelimit)

    return ret


def identify(dn, attr, canonical=False):
    # type: (str, univention.admin.handlers._Attributes, bool) -> None
    pass
