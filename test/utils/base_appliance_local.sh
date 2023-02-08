# shellcheck shell=bash
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2023 Univention GmbH
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

set -e -u -x

TMPDIR="/var/tmp"
APPSDIR="/var/univention/buildsystem2/mirror/appcenter.test/univention-apps"

_ssh () {
	ssh -o BatchMode=yes -n "$@"
}


_scp () {
	scp -B "$@"
}


_kvm_image () {
	local identify="$1"
	_ssh "${IMAGE_SERVER}" "
		set -e -u -x
		install -m 2775 -d '$APPS_BASE'
		cd '$APPS_BASE'
		rm -f '${TMP_KVM_IMAGE}.kv' '$KVM_IMAGE'
		cp '${TMP_KVM_IMAGE}' '${TMP_KVM_IMAGE}.kv'
		guestfish add '${TMP_KVM_IMAGE}.kv' : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		cp -f '${TMP_KVM_IMAGE}.kv' '$KVM_IMAGE'
		md5sum '${KVM_IMAGE}' > '${KVM_IMAGE}.md5'
		sha256sum '${KVM_IMAGE}' > '${KVM_IMAGE}.sha256'
		chmod 644 '${KVM_IMAGE}'*
		rm -f '${TMP_KVM_IMAGE}.kv'
	"
}


_vmplayer_image () {
	local identify="$1"
	_ssh "${IMAGE_SERVER}" "
		set -e -u -x
		install -m 2775 -d '$APPS_BASE'
		cd '$APPS_BASE'
		rm -f '${TMP_KVM_IMAGE}.vm' '${VMPLAYER_IMAGE}'
		cp '${TMP_KVM_IMAGE}' '${TMP_KVM_IMAGE}.vm'
		guestfish add '${TMP_KVM_IMAGE}.vm' : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m '$MEMORY' -p UCS -v '$IMAGE_VERSION' -o --vmware -s '${TMP_KVM_IMAGE}.vm' -f '${VMPLAYER_IMAGE}'
		md5sum '${VMPLAYER_IMAGE}' > '${VMPLAYER_IMAGE}.md5'
		sha256sum '${VMPLAYER_IMAGE}' > '${VMPLAYER_IMAGE}.sha256'
		chmod 644 '${VMPLAYER_IMAGE}'*
		rm -f '${TMP_KVM_IMAGE}.vm'
	"
}


_virtualbox_image () {
	local identify="$1"
	local VGT='/var/tmp/install-vbox-guesttools.sh'
	_scp utils/install-vbox-guesttools.sh "${IMAGE_SERVER}:${VGT}"
	_ssh "${IMAGE_SERVER}" "
		set -e -u -x
		install -m 2775 -d '$APPS_BASE'
		cd '$APPS_BASE'
		rm -f '${TMP_KVM_IMAGE}.vb' '${VBOX_IMAGE}'
		cp '${TMP_KVM_IMAGE}' '${TMP_KVM_IMAGE}.vb'
		guestfish add '${TMP_KVM_IMAGE}.vb' : set-network true : run : mount /dev/mapper/vg_ucs-root / : copy-in ${VGT} /root/ : command /root/install-vbox-guesttools.sh
		guestfish add '${TMP_KVM_IMAGE}.vb' : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m '$MEMORY' -p UCS -v '$IMAGE_VERSION' -o --ova-virtualbox -s '${TMP_KVM_IMAGE}.vb' -f '${VBOX_IMAGE}'
		md5sum '${VBOX_IMAGE}' > '${VBOX_IMAGE}.md5'
		sha256sum '${VBOX_IMAGE}' > '${VBOX_IMAGE}.sha256'
		chmod 644 '${VBOX_IMAGE}'*
		rm -f '${TMP_KVM_IMAGE}.vb' '${VGT}'
	"
}


_esxi () {
	local identify="$1"
	_ssh "${IMAGE_SERVER}" "
		set -e -u -x
		install -m 2775 -d '$APPS_BASE'
		cd '$APPS_BASE'
		rm -f '${TMP_KVM_IMAGE}.es' '${ESX_IMAGE}'
		cp '${TMP_KVM_IMAGE}' '${TMP_KVM_IMAGE}.es'
		guestfish add '${TMP_KVM_IMAGE}.es' : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		generate_appliance -m '$MEMORY' -p UCS -v '$IMAGE_VERSION' -o --ova-esxi -s '${TMP_KVM_IMAGE}.es' -f '${ESX_IMAGE}'
		md5sum '${ESX_IMAGE}' > '${ESX_IMAGE}.md5'
		sha256sum '${ESX_IMAGE}' > '${ESX_IMAGE}.sha256'
		chmod 644 '${ESX_IMAGE}'*
		rm -f '${TMP_KVM_IMAGE}.es'
	"
}


_hyperv_image () {
	local identify="$1"
	_ssh "${IMAGE_SERVER}" "
		set -e -u -x
		install -m 2775 -d '$APPS_BASE'
		cd '$APPS_BASE'
		rm -f '${TMP_KVM_IMAGE}.hv' '${HYPERV_IMAGE_BASE}.vhdx' '${HYPERV_IMAGE_BASE}.zip'
		cp '${TMP_KVM_IMAGE}' '${TMP_KVM_IMAGE}.hv'
		guestfish add '${TMP_KVM_IMAGE}.hv' : run : mount /dev/mapper/vg_ucs-root / : command \"/usr/sbin/ucr set updater/identify='$identify'\"
		qemu-img convert -p -o subformat=dynamic -O vhdx '${TMP_KVM_IMAGE}.hv' '${HYPERV_IMAGE_BASE}.vhdx'
		zip '${HYPERV_IMAGE_BASE}.zip' '${HYPERV_IMAGE_BASE}.vhdx'
		md5sum '${HYPERV_IMAGE_BASE}.zip' > '${HYPERV_IMAGE_BASE}.zip.md5'
		sha256sum '${HYPERV_IMAGE_BASE}.zip' > '${HYPERV_IMAGE_BASE}.zip.sha256'
		chmod 644 '${HYPERV_IMAGE_BASE}'*
		rm -f '${TMP_KVM_IMAGE}.hv' '${HYPERV_IMAGE_BASE}.vhdx'
	"
}


_ec2_image () {
	# Identifier already set
	_ssh "${IMAGE_SERVER}" "generate_appliance --only --ec2-ebs -s '${TMP_KVM_IMAGE}' -v '${UCS_VERSION_INFO}'"
}

# (app|ec2)-appliance
_set_global_vars () {
	APP_ID="${1:?}"
	KVM_USER="${2:?}"
	KVM_SERVER="${KVM_USER}@${3:?}"
	UCS_VERSION="${4:?}"
	UCS_VERSION_INFO="${5?}"

	APPS_SERVER="${KVM_USER}@omar.knut.univention.de"
	IMAGE_SERVER="${KVM_USER}@docker.knut.univention.de"

	APPS_BASE="${APPSDIR}/${UCS_VERSION}/${APP_ID}"
	TMP_KVM_IMAGE="${TMPDIR}/app-appliance-${APP_ID}.qcow2"
	IMAGE_VERSION="${UCS_VERSION}-with-${APP_ID}"
	VMPLAYER_IMAGE="Univention-App-${APP_ID}-vmware.zip"
	KVM_IMAGE="Univention-App-${APP_ID}-KVM.qcow2"
	VBOX_IMAGE="Univention-App-${APP_ID}-virtualbox.ova"
	ESX_IMAGE="Univention-App-${APP_ID}-ESX.ova"
	HYPERV_IMAGE_BASE="Univention-App-${APP_ID}-Hyper-V"
}

# Used by scenarios/app-appliance.cfg
create_app_images () {
	_set_global_vars "$@"

	_convert_image

	MEMORY=$(_ssh "${IMAGE_SERVER}" "virt-cat -a '${TMP_KVM_IMAGE}' /.memory 2>/dev/null || echo 2048")
	IDENTIFIER=$(_ssh "${IMAGE_SERVER}" "virt-cat -a '${TMP_KVM_IMAGE}' /.identifier 2>/dev/null || echo '$APP_ID'")

	# copy to image convert server for later steps and remove tmp image from kvm server
	_scp "${KVM_SERVER}:/${TMP_KVM_IMAGE}" "${IMAGE_SERVER}:${TMP_KVM_IMAGE}"

	_kvm_image "Univention App ${UCS_VERSION} Appliance ${IDENTIFIER} (KVM)"
	_vmplayer_image "Univention App ${UCS_VERSION} Appliance ${IDENTIFIER} (VMware)"
	_esxi "Univention App ${UCS_VERSION} Appliance ${IDENTIFIER} (ESX)"
	_virtualbox_image "Univention App ${UCS_VERSION} Appliance ${IDENTIFIER} (VirtualBox)"

	# cleanup
	_ssh "${KVM_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"
	_ssh "${IMAGE_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"

	# update current link and sync test mirror
	_ssh "$APPS_SERVER" "
		set -e -u -x
		cd '${APPSDIR}'
		test -L 'current/${APP_ID}' && rm 'current/${APP_ID}'
		ln -s '${UCS_VERSION}/${APP_ID}' 'current/${APP_ID}'
		sudo update_mirror.sh -v 'appcenter.test/univention-apps/${UCS_VERSION}/${APP_ID}' 'appcenter.test/univention-apps/current/${APP_ID}'
	"
}

# Used by scenarios/appliances/ucs-appliance.cfg
create_ucs_images () {
	UPDATER_ID="${1:?}"
	KVM_USER="${2:?}"
	KVM_SERVER="${KVM_USER}@${3:?}"
	UCS_VERSION="${4:?}"

	APPS_SERVER="${KVM_USER}@omar.knut.univention.de"
	IMAGE_SERVER="${KVM_USER}@docker.knut.univention.de"

	MEMORY=2048

	APPS_BASE="/var/univention/buildsystem2/temp/build/appliance/"
	TMP_KVM_IMAGE="$TMPDIR/ucs-appliance-master.qcow2"
	IMAGE_VERSION="${UCS_VERSION}"
	VMPLAYER_IMAGE="UCS-VMware-Image.zip"
	KVM_IMAGE="UCS-KVM-Image.qcow2"
	VBOX_IMAGE="UCS-Virtualbox-Image.ova"
	ESX_IMAGE="UCS-VMware-ESX-Image.ova"
	HYPERV_IMAGE_BASE="UCS-Hyper-V-Image"

	_convert_image

	# copy to image convert server for later steps and remove tmp image from kvm server
	_scp "${KVM_SERVER}:/${TMP_KVM_IMAGE}" "${IMAGE_SERVER}:${TMP_KVM_IMAGE}"

	_kvm_image "$UPDATER_ID (KVM)"
	_vmplayer_image "$UPDATER_ID (VMware)"
	_esxi "$UPDATER_ID (ESX)"
	_virtualbox_image "$UPDATER_ID (VirtualBox)"
	_hyperv_image "$UPDATER_ID (HyperV)"

	# cleanup
	_ssh "${KVM_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"
	_ssh "${IMAGE_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"

	echo "## Images available at $APPS_BASE"
}

# Used by scenarios/appliances/ec2-appliance.cfg
create_ec2_image () {
	_set_global_vars "$@"

	_convert_image

	# copy to image convert server for later steps and remove tmp image from kvm server
	_scp "${KVM_SERVER}:${TMP_KVM_IMAGE}" "${IMAGE_SERVER}:${TMP_KVM_IMAGE}"

	_ec2_image

	# cleanup
	_ssh "${KVM_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"
	_ssh "${IMAGE_SERVER}" "rm -f '${TMP_KVM_IMAGE}'"
}

_convert_image () {
	_ssh "${KVM_SERVER:?}" "
		set -e -u -x
		img=\"\$(virsh dumpxml '${KVM_NAME:?}' | xmllint --xpath 'string(/domain/devices/disk[@device=\"disk\"]/source/@file)' -)\"
		qemu-img convert -p -c -O qcow2 \"\${img:?}\" '${TMP_KVM_IMAGE:?}'
	"
}
