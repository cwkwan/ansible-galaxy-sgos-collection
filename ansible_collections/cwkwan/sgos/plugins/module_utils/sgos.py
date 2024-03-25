#
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import Connection, ConnectionError


def get_connection(module):
    """Get device connection

    Creates reusable SSH connection to the device.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        An instance of `ansible.module_utils.connection.Connection` with a
        connection to the device described in the provided module.

    Raises:
        AnsibleConnectionFailure: An error occurred connecting to the device
    """
    if hasattr(module, 'sgos_connection'):
        return module.sgos_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get('network_api')
    if network_api == 'cliconf':
        module.sgos_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg='Invalid connection type %s' % network_api)

    return module.sgos_connection


def get_capabilities(module):
    """Get device capabilities

    Collects and returns a python object with the device capabilities.

    Args:
        module: A valid AnsibleModule instance.

    Returns:
        A dictionary containing the device capabilities.
    """
    if hasattr(module, 'sgos_capabilities'):
        return module.sgos_capabilities

    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'))
    module.sgos_capabilities = json.loads(capabilities)
    return module.sgos_capabilities


def run_commands(module, commands):
    """Run command list against connection.

    Get new or previously used connection and send commands to it one at a time,
    collecting response.

    Args:
        module: A valid AnsibleModule instance.
        commands: Iterable of command strings.

    Returns:
        A list of output strings.
    """
    responses = list()
    connection = get_connection(module)

    for cmd in to_list(commands):
        if isinstance(cmd, dict):
            command = cmd['command']
            prompt = cmd['prompt']
            answer = cmd['answer']
        else:
            command = cmd
            prompt = None
            answer = None

        try:
            out = connection.get(command, prompt, answer)
            out = to_text(out, errors='surrogate_or_strict')
        except ConnectionError as exc:
            module.fail_json(msg=to_text(exc))
        except UnicodeError:
            module.fail_json(msg=u'Failed to decode output from %s: %s' % (cmd, to_text(out)))

        responses.append(out)

    return responses


def load_config(module, commands):
    """Apply a list of commands to a device.

    Given a list of commands apply them to the device to modify the
    configuration in bulk.

    Args:
        module: A valid AnsibleModule instance.
        commands: Iterable of command strings.

    Returns:
        None
    """
    connection = get_connection(module)

    try:
        resp = connection.edit_config(commands)
        return resp.get('response')
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))
