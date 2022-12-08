#!/bin/bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2022 Univention GmbH
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

set -x

install_bb_api () {
  # do not rename function: used as install_[ENV:TEST_API]_api in autotest-241-ucsschool-HTTP-API.cfg
  ucr set bb/http_api/users/django_debug=yes bb/http_api/users/wsgi_server_capture_output=yes bb/http_api/users/wsgi_server_loglevel=debug bb/http_api/users/enable_session_authentication=yes tests/ucsschool/http-api/bb=yes
  cp -v /usr/share/ucs-school-import/configs/ucs-school-testuser-http-import.json /var/lib/ucs-school-import/configs/user_import.json
  python -c 'import json; fp = open("/var/lib/ucs-school-import/configs/user_import.json", "r+w"); config = json.load(fp); config["configuration_checks"] = ["defaults", "mapped_udm_properties"]; config["mapped_udm_properties"] = ["phone", "e-mail", "organisation"]; fp.seek(0); json.dump(config, fp, indent=4, sort_keys=True); fp.close()'
  echo -e "deb [trusted=yes] http://192.168.0.10/build2/ ucs_4.4-0-min-brandenburg/all/\ndeb [trusted=yes] http://192.168.0.10/build2/ ucs_4.4-0-min-brandenburg/amd64/" > /etc/apt/sources.list.d/30_BB.list
  univention-install -y ucs-school-http-api-bb
  # shellcheck disable=SC2009
  ps aux | grep api-bb
}

install_kelvin_api () {
  # do not rename function: used as install_[ENV:TEST_API]_api in autotest-241-ucsschool-HTTP-API.cfg
  # shellcheck disable=SC2015
  . utils.sh && switch_to_test_app_center || true
  echo -n univention > /tmp/univention
  # use brach image if given
  if [ -n "$UCS_ENV_KELVIN_IMAGE" ]; then
    if [[ $UCS_ENV_KELVIN_IMAGE =~ ^gitregistry.knut.univention.de.* ]]; then
        docker login -u "$GITLAB_REGISTRY_TOKEN" -p "$GITLAB_REGISTRY_TOKEN_SECRET" gitregistry.knut.univention.de
    fi
    univention-app dev-set ucsschool-kelvin-rest-api "DockerImage=$UCS_ENV_KELVIN_IMAGE"
  fi
  univention-app install --noninteractive --username Administrator --pwdfile /tmp/univention ucsschool-kelvin-rest-api
  docker images
  docker ps -a
  univention-app shell ucsschool-kelvin-rest-api ps aux
}

install_mv_idm_gw_sender_ext_attrs () {
  local lb
  lb="$(ucr get ldap/base)"
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="mvDst" \
    --set CLIName="mvDst" \
    --set shortDescription="mvDst" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=1 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute13 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=1
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="UUID" \
    --set CLIName="UUID" \
    --set shortDescription="UUID" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute14 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="mvStaffType" \
    --set CLIName="mvStaffType" \
    --set shortDescription="mvStaffType" \
    --set module="users/user" \
    --set syntax=string \
    --set default="" \
    --set multivalue=1 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute15 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
}

install_mv_idm_gw_receiver_ext_attrs () {
  local lb
  lb="$(ucr get ldap/base)"
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="stamm_dienststelle" \
    --set CLIName="stamm_dienststelle" \
    --set shortDescription="Stammdienststelle" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set tabName="UCS@school" \
    --set tabPosition=9 \
    --set groupName="IDM Gateway" \
    --set groupPosition="1" \
    --append translationGroupName='"de_DE" "IDM Gateway"' \
    --append translationGroupName='"fr_FR" "Passerelle IDM"' \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute13 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="idm_gw_last_update" \
    --set CLIName="idm_gw_last_update" \
    --set shortDescription="Date of last update by the IDM GW" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set tabName="UCS@school" \
    --set tabPosition=9 \
    --set groupName="IDM Gateway" \
    --set groupPosition="2" \
    --append translationGroupName='"de_DE" "IDM Gateway"' \
    --append translationGroupName='"fr_FR" "Passerelle IDM"' \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute14 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=0
  udm settings/extended_attribute create \
    --ignore_exists \
    --position "cn=custom attributes,cn=univention,${lb}" \
    --set name="idm_gw_pw_sync" \
    --set CLIName="idm_gw_pw_sync" \
    --set shortDescription="IDM Gateway password sync" \
    --set module="users/user" \
    --append options="ucsschoolStudent" \
    --append options="ucsschoolTeacher" \
    --append options="ucsschoolStaff" \
    --append options="ucsschoolAdministrator" \
    --set syntax=string \
    --set default="" \
    --set multivalue=0 \
    --set valueRequired=0 \
    --set mayChange=1 \
    --set doNotSearch=1 \
    --set objectClass=univentionFreeAttributes \
    --set ldapMapping=univentionFreeAttribute15 \
    --set deleteObjectClass=0 \
    --set overwriteTab=0 \
    --set fullWidth=1 \
    --set disableUDMWeb=1
}

add_pre_join_hook_to_install_from_test_appcenter () {
	# do not use univention-appcenter-dev, if we have a pending appcenter errata update
	# this new version is used on the dvd, but at this point we can't install errata-test
	# packages and so installing univention-appcenter-dev might fail due to compatibility
	# reasons (dvd: errata-test univention-appcenter vs univention-appcenter-dev from release
	# errata packages)
	cat <<-'EOF' >"/tmp/appcenter-test.sh"
#!/bin/sh
ucr set repository/app_center/server='appcenter-test.software-univention.de' update/secure_apt='false' appcenter/index/verify='no'
univention-app update
exit 0
EOF
	# shellcheck source=/dev/null
	. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension \
		--binddn "cn=admin,$(ucr get ldap/base)" \
		--bindpwdfile=/etc/ldap.secret \
		--packagename dummy \
		--packageversion "1.0" \
		--data /tmp/appcenter-test.sh \
		--data_type="join/pre-join"
}

add_pre_join_hook_to_install_from_test_repository () {
	# activate test repository for school-replica join
	cat <<-'EOF' >"/tmp/repo-test.sh"
#!/bin/sh
ucr set repository/online/server='updates-test.knut.univention.de'
exit 0
EOF
	# shellcheck source=/dev/null
	. /usr/share/univention-lib/ldap.sh && ucs_registerLDAPExtension \
		--binddn "cn=admin,$(ucr get ldap/base)" \
		--bindpwdfile=/etc/ldap.secret \
		--packagename setrepo \
		--packageversion "1.0" \
		--data /tmp/repo-test.sh \
		--data_type="join/pre-join"
}

create_virtual_schools () {
	local number_of_schools=${1:?missing number of schools to create}
	local formated_school_number
	rm -f ./virtual_schools.txt
	for ((i=1; i <= number_of_schools; i++)); do
		printf -v formated_school_number "%0${#number_of_schools}d" "$i"
		/usr/share/ucs-school-import/scripts/create_ou --verbose "SchoolVirtual$formated_school_number" "r300-sV$formated_school_number" --displayName "SchuleVirtual$formated_school_number"
		printf "SchoolVirtual%0${#number_of_schools}d\n" "$i" >> ./virtual_schools.txt  # Later used for the import script
	done
}


# used in scenarios/kvm-templates/schoolprimary-with-100000-users-kvm-template.cfg
create_users_in_template_job () {
	# don't delete users
	cat <<EOF > /var/lib/ucs-school-import/configs/user_import.json
{
  "no_delete": true
}
EOF
	# fix record_uid
	sed -i 's/"record_uid": "<firstname>.<lastname>"/"record_uid": "<firstname>.<lastname>.<username>"/' \
		/usr/share/ucs-school-import/configs/ucs-school-testuser-import.json
	# add import hook
	cat <<EOF > /usr/share/ucs-school-import/pyhooks/testimport.py
from ucsschool.importer.utils.user_pyhook import UserPyHook

class MyHook(UserPyHook):

    priority = {
        "pre_create": 1,
    }

    def pre_create(self, user):
        user.password = "univention"
        mapping = {
            "staff": "generic_user",
        }
        custome_roles = []
        for role in user.ucsschool_roles:
            role, context, school = role.split(":")
            custome_roles.append(f"{mapping.get(role, role)}:bsb:{school}")
        user.ucsschool_roles += custome_roles

EOF
	# create schools
	school_count=400
	schools_big=()
	schools_normal=()
	for i in $(seq 1 "$school_count"); do
		/usr/share/ucs-school-import/scripts/create_ou "--verbose" "school$i" "replica$i" >/tmp/import.log 2>&1 || return 1
		if [ "$i" -le 60 ]; then
			schools_big+=("school$i")
		else
			schools_normal+=("school$i")
		fi
	done
	# 60 big schools with 3000 students and 50 classes
	/usr/share/ucs-school-import/scripts/ucs-school-testuser-import \
		--classes 3000 \
		--students 180000 \
		--teachers 15000 \
		--staff 1500 \
		"${schools_big[@]}" >/tmp/import.log 2>&1 || return 1
	# 340 normal schools with 250 students and 10 classes
	/usr/share/ucs-school-import/scripts/ucs-school-testuser-import \
		--classes 3400 \
		--students 85000 \
		--teachers 15000 \
		--staff 1500 \
		"${schools_normal[@]}" >/tmp/import.log 2>&1 || return 1
	rm -f /tmp/import.log
	# clean up
	rm -f /usr/share/ucs-school-import/pyhooks/testimport.py
	rm -f /var/lib/ucs-school-import/configs/user_import.json
	# add some more
	# * workgroups, 10 work groups per school with 60 members each
	# * class groups, 1500 empty classes to the 60 big schools
	python3 - <<"EOF" || return 1
from ucsschool.lib.models import School, User
from ucsschool.lib.models.group import SchoolClass, WorkGroup
from univention.admin.uldap import getAdminConnection

import random

lo, po = getAdminConnection()
schools = School.get_all(lo)

for school in schools:
    if school.name == "DEMOSCHOOL":
        continue
    users = [user.dn for user in User.get_all(lo, school.name)]
    # add workgroups to every school
    for i in range(1, 11):
        wg_data = {
            "name": f"{school.name}-workgroup{i}",
            "school": school.name,
            "users": random.sample(users, 60),
        }
        wg = WorkGroup(**wg_data)
        wg.create(lo)
    # add empty classes in big schools
    if len(users) > 2000:
        for i in range(1, 1501):
            sc_data = {"name": f"{school.name}-empty-class{i}", "school": school.name}
            sc = SchoolClass(**sc_data)
            sc.create(lo)
EOF


}

# get first 60 schools as python diskcache
create_and_copy_test_data_cache () {
	local root_password="${1:?missing root password}"
	univention-install -y python3-pip sshpass
	pip3 install diskcache
	python3 - <<"EOF" || return 1
from ucsschool.lib.models import School, User, Group
from univention.admin.uldap import getAdminConnection
from diskcache import Index

CACHE_PATH = "/var/lib/test-data"

lo, po = getAdminConnection()
db = Index(str(CACHE_PATH))
db["schools"] = [ f"school{i}" for i in range(1, 61) ]

for i in range(1, 61):
    school = School(f"school{i}")
    print(school)
    data = {
        "users": {},
        "groups": {},
        "students": {},
        "teachers": {},
        "staff": {},
        "admins": {},
        "classes": [],
        "workgroups": [],
    }
    for user in User.get_all(lo, school.name):
        data["users"][user.name] = user.to_dict()
        if user.is_student(lo):
            data["students"][user.name] = user.dn
        elif user.is_teacher(lo):
            data["teachers"][user.name] = user.dn
        elif user.is_staff(lo):
            data["staff"][user.name] = user.dn
        elif user.is_administrator(lo):
            data["admins"][user.name] = user.dn
    for group in Group.get_all(lo, school.name):
        # only non-empty groups
        if len(group.users) == 0:
            continue
        data["groups"][group.name] = group.to_dict()
        if group.self_is_workgroup():
            data["workgroups"].append(group.name)
        elif group.self_is_class():
            data["classes"].append(group.name)
    db[school.name] = data
db.cache.close()
EOF

	shift
	for ip in "$@"; do
		sshpass -p "$root_password" scp -r  -o StrictHostKeyChecking=no -o UpdateHostKeys=no /var/lib/test-data root@"$ip":/var/lib/ || return 1
	done
}
