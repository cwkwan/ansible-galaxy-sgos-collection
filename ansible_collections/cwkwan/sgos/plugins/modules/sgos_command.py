#!/usr/bin/python
#
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
---
module: sgos_command
version_added: "2.9"
author: "cwkwan@gmail.com"
short_description: Run commands on remote devices running Proxy SGOS
description:
  - Sends arbitrary commands to a SGOS device and returns the results
    read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
  - It is not tested but you could run configuration commands with this module.
    Please use M(sgos_config) to configure SGOS devices.
notes:
  - Tested against SGOS 6.7.4.144, Ansible 2.9.1
  - If a command sent to the device requires answering a prompt, it is possible
    to pass a dict containing I(command), I(answer) and I(prompt). See examples.
options:
  commands:
    description:
      - List of commands to send to remote SGOS device. The
        resulting output from the command is returned. If
        I(wait_for) argument is provided, the module does
        not return until the condition is satisfied or reached
        the number of retries.
    required: true
    type: list
  wait_for:
    description:
      - List of conditions to evaluate against the output of the
        command. The task will wait for each condition to be true
        before moving forward. If the conditional is not true
        within the configured number of retries, the task fails.
        See examples.
    type: list
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy. Valid
        values are C(all) or C(any). If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied. If
        the value is set to C(any) then only one of the values must be
        satisfied.
    type: str
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the
        I(wait_for) conditions.
    type: int
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    type: int
    default: 1

EXAMPLES = """
tasks:
  - name: run show version on remote devices
    sgos_command:
      commands: show version

  - name: run show version and check to see if output contains Version
    sgos_command:
      commands: show version
      wait_for: result[0] contains Version

  - name: run multiple commands on remote devices
    sgos_command:
      commands:
        - show version
        - show interfaces all

  - name: run multiple commands and evaluate the output
    sgos_command:
      commands:
        - show version
        - show interface all
      wait_for:
        - result[0] contains Version
        - result[1] contains interface
  - name: run command that requires answering a prompt
    sgos_command:
      commands:
        - command: 'clear sessions'
          prompt: 'This operation will logout all the user sessions. Do you want to continue (yes/no)?:'
          answer: y
  - name: run commands that require entering conf mode
    sgos_command:
      commands:
        - conf t
        - forwarding
        - view
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""

import re
import time

from ansible_collections.cwkwan.sgos.plugins.module_utils.sgos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import ComplexList
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


__metaclass__ = type


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list'),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    result = {'changed': False}

    warnings = list()

    command = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict()
    ), module)
    commands = command(module.params['commands'])

    result['warnings'] = warnings

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        responses = run_commands(module, commands)

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'changed': False,
        'stdout': responses,
        'stdout_lines': list(to_lines(responses))
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
