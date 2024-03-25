#
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
cliconf: sgos
short_description: Use sgos cliconf to run command on Proxy SGOS platform
description:
  - This sgos plugin provides abstraction over CLI interface of Proxy SGOS
    devices. You must have privilege(write) access in order to use this module.
    As Ansible has to intialize the terminal Screen Lines and Columns and that
    requires configuration mode on SGOS.
version_added: "2.9"
notes:
  - Tested against SGOS 6.7.4.144, Ansible 2.9.1
"""

import re
import json

from itertools import chain
from functools import wraps

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.plugins.cliconf import CliconfBase


def exit_conf_first(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        while b'#(config' in self._connection.get_prompt():
            self.send_command('exit')
        return func(self, *args, **kwargs)
    return wrapped


def exit_conf_last(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        function = func(self, *args, **kwargs)

        while b'#(config' in self._connection.get_prompt():
            self.send_command('exit')
        return function
    return wrapped


class Cliconf(CliconfBase):

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'sgos'
        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version:\s+([ \S]+)', data, re.M)
        if match:
            device_info['network_os_version'] = match.group(1)

        reply = self.get('show advanced-url /Diagnostics/Hardware/Info')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Model:\s+(\S+)', data, re.M)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get('show appliance-name')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Appliance name\s+:\s+(\S+)', data, re.M)
        if match:
            device_info['network_os_hostname'] = match.group(1)

        return device_info

    def get_config(self):
        pass

    @exit_conf_first
    @exit_conf_last
    def edit_config(self, command):
        resp = {}
        results = []
        requests = []
        sendonly = False
        eof_marker = '_EOF'

        self.send_command('configure terminal')

        for cmd in chain(to_list(command)):
            if isinstance(cmd, dict):
                command = cmd['command']
                prompt = cmd['prompt']
                answer = cmd['answer']
                eof_marker = cmd['eof_marker']
                newline = cmd.get('newline', True)
            else:
                command = cmd
                prompt = None
                answer = None
                newline = True

            if command.lower() == 'exit':
                mode = self._connection.get_prompt()
                if to_text(mode, errors='surrogate_or_strict').strip().endswith('#'):
                    results.append(to_text('%s ignored, already out of config mode' % command, errors='surrogate_or_strict'))
                    requests.append(cmd)
                    continue

            if command.lower().startswith('inline'):
                sendonly = True

            if command.startswith(eof_marker):
                sendonly = False
                newline = False

            results.append(self.send_command(command, prompt, answer, sendonly, newline))
            requests.append(cmd)

        resp['request'] = requests
        resp['response'] = results

        return resp

    @exit_conf_first
    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        return json.dumps(result)
