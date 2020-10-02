#!/usr/bin/python
# coding: utf-8

# (c) 2018, Jan Christian Grünhage <jan.christian@gruenhage.xyz>
# (c) 2020, Famedly GmbH
# GNU Affero General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/agpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
author: "Jan Christian Grünhage (@jcgruenhage)"
module: matrix_state
short_description: Set matrix room state
description:
    - This module sets matrix room state idempotently
options:
    event_type:
        description:
            - Event type of the state to be set
        required: true
    state_key:
        description:
            - State key for the state event to be set
        required: true
    content:
        description:
            - The content to set the state to
        required: true
    room_id:
        description:
            - ID of the room to set the state for
        required: true
    hs_url:
        description:
            - URL of the homeserver, where the CS-API is reachable
        required: true
    token:
        description:
            - Authentication token for the API call.
        required: true
requirements:
    -  matrix-client (Python library)
'''

EXAMPLES = '''
- name: Set the server ACL for the admin room
  matrix_state:
    event_type: m.room.server_acl
    state_key: ""
    content:
      allow:
        - "*"
      deny:
        - "bad-server.one"
        - "bad-server.two"
    room_id: "!LAVFnosfDouvhA9VEhiuSV:matrix.org"
    hs_url: "https://matrix.org"
    token: "{{ matrix_auth_token }}"
'''

RETURN = '''
event_id:
    description:
        - ID of the created event
    returned: changed
    type: str
    sample: $Het2Dv7EEDFNJNgY-ehLSUrdqMo8JOxZDCMnuQPSNfo
'''
import traceback
import asyncio

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

MATRIX_IMP_ERR = None
try:
    from nio import AsyncClient, RoomGetStateEventResponse, RoomPutStateResponse, JoinedRoomsError
except ImportError:
    MATRIX_IMP_ERR = traceback.format_exc()
    MATRIX_FOUND = False
else:
    MATRIX_FOUND = True


async def run_module():
    module_args = dict(
        event_type=dict(type='str', required=True),
        state_key=dict(type='str', required=True),
        content=dict(type='dict', required=True),
        room_id=dict(type='str', required=True),
        hs_url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not MATRIX_FOUND:
        module.fail_json(msg=missing_required_lib('matrix-nio'), exception=MATRIX_IMP_ERR)

    if module.check_mode:
        # TODO: Do proper check
        return result

    # create a client object
    client = AsyncClient(module.params['hs_url'])
    client.access_token = module.params['token']

    failed = False
    result = {}

    # Check if already in room
    rooms_resp = await client.joined_rooms()
    if isinstance(rooms_resp, JoinedRoomsError):
        failed = True
        result = {"msg":"Couldn't get joined rooms."}
    elif module.params['room_id'] not in rooms_resp.rooms:
        failed = True
        result = {"msg": "Not in the room you're trying to set state for."}
    else:
        # Fetch state from room
        state_resp = await client.room_get_state_event(
            module.params['room_id'],
            module.params['event_type'],
            module.params['state_key']
        )
        # If successful, compare with content from module and content is the same, return with changed=false and the ID of the old event
        if isinstance(state_resp, RoomGetStateEventResponse) and state_resp.content == module.params['content']:
            result = {"changed": False}
        # Else, try to send a new state event
        else:
            send_resp = await client.room_put_state(
                module.params['room_id'],
                module.params['event_type'],
                module.params['content'],
                module.params['state_key']
            )
            # If successful, return with changed=true and the ID of the new event
            if isinstance(send_resp, RoomPutStateResponse):
                result = {"event_id": send_resp.room_id, "changed": True}
            # Else, fail
            else:
                failed = True
                result = {"msg": "Couldn't set state: {error}".format(error=send_resp)}

    await client.close()

    if failed:
        module.fail_json(**result)
    else:
        module.exit_json(**result)

def main():
    asyncio.run(run_module())


if __name__ == '__main__':
    main()
