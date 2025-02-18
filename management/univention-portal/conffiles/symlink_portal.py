#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2021-2024 Univention GmbH
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

import os
import os.path
from errno import EEXIST


portal_path = "/usr/share/univention-portal"


def handler(config_registry, changes):
    old, new = changes['portal/paths']
    old = [o.strip() for o in old.split(",")] if old else []
    new = [n.strip() for n in new.split(",")] if new else []
    for path in old:
        if path in new:
            continue
        path = os.path.normpath("/var/www" + path)
        if not os.path.islink(path) or os.path.realpath(path) != portal_path:
            print(f"{path} does not link to the portal contents. Skipping...")
        else:
            print(f"Removing portal link to {path}...")
            os.unlink(path)
    for path in new:
        if path in old:
            continue
        path = os.path.normpath("/var/www" + path)
        if os.path.islink(path):
            link_target = os.path.realpath(path)
            print(f"{path} already links (to {link_target}). Skipping...")
        else:
            print(f"Linking {path} to portal content...")
            try:
                dirname = os.path.dirname(path)
                try:
                    os.makedirs(dirname)
                except OSError as exc:
                    if exc.errno != EEXIST:
                        raise
            except OSError as exc:
                print(f"Error creating {dirname}: {exc}!")
            else:
                try:
                    os.symlink(portal_path, path)
                except OSError as exc:
                    print(f"Error creating a link from {path} to {portal_path}: {exc}!")
