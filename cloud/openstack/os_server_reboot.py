#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2016, eBay Software Foundation
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


DOCUMENTATION = '''
---
module: os_server_reboot
short_description: Reboots a Compute Instance on OpenStack
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Auston McReynolds (@amcrn)"
description:
   - Reboot an existing compute instance from OpenStack.
     This module does not return any data other than changed true/false.
options:
   server:
     description:
        - Name or ID of the instance
     required: true
   wait:
     description:
        - If the module should wait for the reboot to complete.
     required: false
     default: 'yes'
   timeout:
     description:
        - The amount of time the module should wait for the reboot to complete.
     required: false
     default: 180
   type:
     description:
       - Perform a reboot of this type.
     choices: [soft, hard]
     required: false
     default: soft
requirements:
    - "python >= 2.6"
    - "shade"
'''


EXAMPLES = '''
# Reboots a compute instance
- os_server_reboot:
       server: vm1
       type: soft
       auth:
         auth_url: https://host:5443/v2.0
         username: admin
         password: admin
         project_name: admin
'''


RETURN = '''
#
'''


def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        type=dict(default='soft', choices=['soft', 'hard']),
        wait=dict(default=False, type='bool'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, supports_check_mode=True, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:

        cloud = shade.operator_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        if not server:
            module.fail_json(msg='Could not find server %s' % server)

        if module.check_mode:
            module.exit_json(changed=server.status not in ('REBOOT', 'HARD_REBOOT'))

        # server is already rebooting from a different request, return false
        if server.status in ('REBOOT', 'HARD_REBOOT'):
            module.exit_json(changed=False)

        cloud.nova_client.servers.reboot(server.id, reboot_type=module.params['type'].upper())

        if not module.params['wait']:
            return module.exit_json(changed=True)

        # after the reboot action has been accepted, it's possible that the status is
        # still 'active' for a very short period of time until flipping to 'reboot' or
        # 'hard_reboot'. therefore, sleep for a bit before running the checks.
        #
        # note: checking for a 'has ever been in reboot state' is not fool-proof because
        # some soft reboots finish in sub one second.

        import time
        time.sleep(2)

        for count in shade._utils._iterate_timeout(module.params['timeout'],
                                                   "Timeout waiting for server to complete reboot."):
            try:
                check_server = cloud.get_server(module.params['server'])
            except Exception:
                continue

            if check_server.status == 'ACTIVE':
                module.exit_json(changed=True)

            if check_server.status == 'ERROR':
                module.fail_json(msg="Server reached ERROR state while rebooting.")

        module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
