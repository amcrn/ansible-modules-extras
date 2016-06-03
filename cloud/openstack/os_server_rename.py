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
module: os_server_rename
short_description: Renames a Compute Instance on OpenStack
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Auston McReynolds (@amcrn)"
description:
   - Rename an existing compute instance from OpenStack.
     This module does not return any data other than changed true/false.
options:
   server:
     description:
        - Name or ID of the instance
     required: true
   name:
     description:
        - The new name for the instance
     required: true
requirements:
    - "python >= 2.6"
    - "shade"
'''


EXAMPLES = '''
# Renames a compute instance
- os_server_rename:
       server: vm1
       name: newName
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
        name=dict(required=True),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, supports_check_mode=True, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    name = module.params['name']

    try:

        cloud = shade.operator_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        if not server:
            module.fail_json(msg='Could not find server %s' % server)

        if server.name == name:
            module.exit_json(changed=False)

        if module.check_mode:
            module.exit_json(changed=True)

        cloud.nova_client.servers.update(server.id, name=name)

        module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
