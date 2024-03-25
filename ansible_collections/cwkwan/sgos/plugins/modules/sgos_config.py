#!/usr/bin/python
#
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = """
---
module: sgos_config
version_added: "2.9"
author: "cwkwan@gmail.com"
short_description: Run config commands on remote devices running Proxy SGOS
description:
  - This module provides an implementation for working with SGOS configuration.
notes:
  - Tested against SGOS 6.7.4.144, Ansible 2.9.1
options:
  lines:
    description:
      - Ordered lines of commands or configurations exactly as you would type
        in command prompt, except do not include the enable and conf t
        sequence. Optinal to include the outer Exit.
        It is possible to pass a dict containing I(command), I(answer), and
        I(prompt) to detect and answer prompt for specific command.
    type: list
    aliases: ['commands']
  src:
    description:
      - Specifies source path to the file that contains the configuration
        or configuration template. The path to the source file can either
        be the full path on the Ansible control host or a relative path
        from the playbook or role root directory.
        This argument is mutually exclusive with I(lines).
    type: path
  prompt:
    description:
      - A single regex pattern or a sequence of patterns to evaluate the expected
        prompt from I(command), I(src), or I(lines).
      - You cannot specify I(prompt) for both I(command) and I(src) / I(lines).
      - All I(prompt) and I(answer) will apply to all commands when specified
        on I(src) / I(lines).
    required: false
    type: list
  answer:
    description:
      - The answer to reply with if I(prompt) is matched. The value can be a single answer
        or a list of answer for multiple prompts. In case the command execution results in
        multiple prompts the sequence of the prompt and excepted answer should be in same order.
      - You cannot specify I(answer) for both I(command) and I(src) / I(lines).
      - All I(prompt) and I(answer) will apply to all commands when specified
        on I(src) / I(lines).
    required: false
    type: list
  eof_marker:
    description:
      - This is only meaningful for inline config The I(eof_marker) tells ansible to treat the
        command line from I(lines) / I(src) as end of inline config block if the line starts with
        I(eof_marker)
      - EOF for inline config should be a single command on it's own line.
    type: str
    default: "_EOF"
"""

EXAMPLES = """
- name: Module does not differentite command from configuration
  sgos_config:
    lines: show ver

- name: Set DNS
  sgos_config:
    lines:
      - dns clear server
      - dns server 10.219.96.1
      - dns server 10.219.96.2
      - dns server 10.220.96.1

- name: load config from file
  sgos_config:
    src: /path/to/config.template
"""

RETURN = """
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['ntp clear', 'ntp server 10.219.96.2', 'ntp interval 5']
"""

import re

from ansible_collections.cwkwan.sgos.plugins.module_utils.sgos import load_config
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types
from ansible.module_utils.network.common.utils import EntityCollection

__metaclass__ = type


def to_lines(response):
    for item in response:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def get_candidate(module):
    contents = module.params['src'] or module.params['lines']

    if module.params['src']:
        context = parse_lines(contents.splitlines())
        commands = []
        inline_block = False
        eof_mark = ''
        for line in context:
            if line.lstrip().lower().startswith('inline') and not inline_block:
                inline_block = True
                inline_cli = line.strip().split()
                eof_mark = inline_cli[-1]
                match = re.search(r'(%s.*?)(%s|$)' % (line, eof_mark), contents, re.DOTALL)
                inline_cmd = match.group(1)
                inline_eof = match.group(2)
                contents = re.sub(r'%s%s' % (re.escape(inline_cmd), re.escape(inline_eof)), '', contents)
                commands.append(inline_cmd)
            else:
                if inline_block and (eof_mark in line):
                    inline_block = False
                    commands.append(eof_mark)
                elif inline_block and (eof_mark not in line):
                    continue
                else:
                    commands.append(line)
        contents = commands

    command_attrs = dict(command=dict(key=True),
                         prompt=dict(type='list', required=False),
                         answer=dict(type='list', required=False))

    parsed_contents = []
    for item in contents:
        parsed_contents.append(parse_prompt(module, item))

    command = EntityCollection(module, command_attrs)
    candidate = command(parsed_contents)

    for item in candidate:
        item['eof_marker'] = module.params['eof_marker']

    return candidate


def parse_prompt(module, item):
    if isinstance(item, dict):
        if ('prompt' in item or 'answer' in item) and module.params['prompt']:
            module.fail_json(
                msg='You cannot set prompt/answer at both task level and line level'
            )
        return item
    else:
        line_dict = {}
        line_dict['command'] = item
        line_dict['prompt'] = module.params['prompt']
        line_dict['answer'] = module.params['answer']
        return line_dict


def parse_lines(contents):
    return [line for line in contents if len(line.strip()) > 0]

def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        src=dict(type='path'),

        lines=dict(aliases=['commands'], type='list'),

        eof_marker=dict(default='_EOF'),

        prompt=dict(type='list', required=False),
        answer=dict(type='list', required=False),
    )

    required_together = [['prompt', 'answer']]

    mutually_exclusive = [('lines', 'src')]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_together=required_together,
                           supports_check_mode=False)

    result = {'changed': False}

    warnings = list()
    result['warnings'] = warnings

    if any((module.params['lines'], module.params['src'])):
        candidate = get_candidate(module)
        result['commands'] = candidate

        if candidate:
            result['response'] = list(to_lines(load_config(module, candidate)))

        # It's changed as long as you sent something unless we check the return
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
