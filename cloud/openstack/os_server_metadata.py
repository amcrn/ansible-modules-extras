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
module: os_server_metadata
short_description: Sets and/or deletes metadata on a Compute Instance on OpenStack
extends_documentation_fragment: openstack
version_added: "2.2"
author: "Auston McReynolds (@amcrn)"
description:
   - Sets and/or deletes the metadata on an existing compute instance from OpenStack.
     This module does not return any data other than changed true/false.
options:
   server:
     description:
        - Name or ID of the instance
     required: true
   set:
     description:
        - A list of key value pairs that should be set as a metadata on
          the instance.
     required: false
     default: None
   delete:
     description:
        - A list of metadata keys to delete from the instance.
     required: false
     default: None
requirements:
    - "python >= 2.6"
    - "shade"
'''


EXAMPLES = '''
# Updates the metadata on a compute instance
- os_server_metadata:
       server: vm1
       set:
         key1: value1
         key2: value2
       delete:
         - key3
         - key4
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
        set=dict(default=None, type='dict'),
        delete=dict(default=None, type='list'),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, supports_check_mode=True, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:

        if not module.params['set']:
            module.params['set'] = {}
        if not module.params['delete']:
            module.params['delete'] = []

        if not module.params['set'] and not module.params['delete']:
            module.exit_json(changed=False)

        cloud = shade.operator_cloud(**module.params)
        server = cloud.get_server(module.params['server'])
        if not server:
            module.fail_json(msg='Could not find server %s' % server)

        has_set_changes = not set(module.params['set'].items()).issubset(set(server.metadata.items()))

        meta_to_delete = []
        for del_key in module.params['delete']:
            if del_key in server.metadata:
                meta_to_delete.append(del_key)

        has_changes = has_set_changes or meta_to_delete

        if module.check_mode:
            module.exit_json(changed=has_changes)

        if not has_changes:
            module.exit_json(changed=False)

        if has_set_changes:
            cloud.nova_client.servers.set_meta(server=server.id, metadata=module.params['set'])

        if meta_to_delete:
            cloud.nova_client.servers.delete_meta(server=server.id, keys=meta_to_delete)

        module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
