#!/usr/share/ucs-test/runner python
## desc: Test appending and removing MAC addresses for all computer roles
## tags: [udm-computers]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.utils as utils


if __name__ == '__main__':
	macAddresses = ('11:11:11:11:11:11', '22:22:22:22:22:22', '33:33:33:33:33:33', '44:44:44:44:44:44')
	
	for role in udm_test.UCSTestUDM.COMPUTER_MODULES:
		with udm_test.UCSTestUDM() as udm:
			for mac in macAddresses: #FIXME: workaround for remaining locks
				udm.addCleanupLock('mac', mac)

			computer = udm.create_object(role, name = uts.random_name(), append = {'mac': macAddresses[:2]})
			if not utils.verify_ldap_object(computer, {'macAddress': macAddresses[:2]}):
				utils.fail('"macAddress" of %s differed from expectation after trying to append %r during creation' % (role, macAddresses[:2]))

			udm.modify_object(role, dn = computer, append = {'mac': macAddresses[2:]})
			if not utils.verify_ldap_object(computer, {'macAddress': macAddresses}):
				utils.fail('"macAddress" of %s differed from expectation after trying to append %r during modification' % (role, macAddresses[2:]))

			udm.modify_object(role, dn = computer, remove = {'mac': macAddresses[:2]})
			if not utils.verify_ldap_object(computer, {'macAddress': macAddresses[2:]}):
				utils.fail('"macAddress" of %s differed from expectation after trying to remove %r during modification' % (role, macAddresses[:2]))
