#!/usr/bin/python
#
#
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: sgos_facts
version_added: "2.9"
author: "cwkwan@gmail.com"
short_description: Collect facts from devices running Proxy SGOS
description:
  - Collects a base set of device facts from a remote device that
    is running SGOS. This module prepends all of the
    base network fact keys with C(ansible_net_<fact>). The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
notes:
  - Tested against SGOS 6.7.4.144, Ansible 2.9.1
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset. Possible values for this argument include
        all, hardware, config, and interfaces. Can specify a list of
        values to include a larger subset. Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    type: list
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- sgos_facts:
    gather_subset: all

# Collect only the config and default facts
- sgos_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- sgos_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: str
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: str
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: str
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: str

# hardware
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int
"""

import re

from ansible_collections.cwkwan.sgos.plugins.module_utils.sgos import run_commands
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = list()

    def __init__(self, module):
        self.module = module
        self.facts = dict()
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, self.COMMANDS)

    def run(self, cmd):
        return run_commands(self.module, cmd)


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show appliance-name',
        'show advanced-url /Diagnostics/Hardware/Info'
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['version'] = self.parse_version(data)
            self.facts['serialnum'] = self.parse_serialnum(data)

        data = self.responses[1]
        if data:
            self.facts['hostname'] = self.parse_hostname(data)

        data = self.responses[2]
        if data:
            self.facts['model'] = self.parse_model(data)

    def parse_version(self, data):
        match = re.search(r'Version: ([ \S]+)', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Model: (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'Appliance name : (\S+)', data, re.M)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial number: (\S+)', data, re.M)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show status'
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['memtotal_mb'] = int(self.parse_memtotal(data))
            self.facts['memfree_mb'] = int(self.parse_memfree(data))

    def parse_memtotal(self, data):
        match = re.search(r'Memory installed:\s+(\d+)\s', data, re.M)
        if match:
            return match.group(1)

    def parse_memfree(self, data):
        match = re.search(r'Memory available:\s+(\d+)\s', data, re.M)
        if match:
            return match.group(1)


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        gather_subset=dict(default=["!config"], type='list')
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset')

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = dict()
    facts['gather_subset'] = list(runable_subsets)

    instances = list()
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = dict()
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    warnings = list()

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()

