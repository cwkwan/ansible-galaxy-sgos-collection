#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from unittest.mock import patch
from ansible_collections.cwkwan.sgos.plugins.modules import sgos_command
from sgos_module import TestSgosModule, load_fixture, set_module_args


class TestSgosCommandModule(TestSgosModule):

    module = sgos_command

    def setUp(self):
        super(TestSgosCommandModule, self).setUp()

        # self.mock_run_commands = patch('ansible.modules.network.sgos.sgos_command.run_commands')
        self.mock_run_commands = patch('ansible_collections.cwkwan.sgos.plugins.modules.sgos_command.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestSgosCommandModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item['command'])
                    command = obj['command']
                except ValueError:
                    command = item['command']
                filename = str(command).replace(' ', '_')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_sgos_command_simple(self):
        set_module_args(dict(commands=['show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Version: SGOS'))

    def test_sgos_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Version: SGOS'))

    def test_sgos_command_wait_for(self):
        wait_for = 'result[0] contains "Version: SGOS"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module()

    def test_sgos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_sgos_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_sgos_command_match_any(self):
        wait_for = ['result[0] contains "SGOS"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='any'))
        self.execute_module()

    def test_sgos_command_match_all(self):
        wait_for = ['result[0] contains "SGOS"',
                    'result[0] contains "Version: SGOS"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='all'))
        self.execute_module()

    def test_sgos_command_match_all_failure(self):
        wait_for = ['result[0] contains "Version: SGOS"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, wait_for=wait_for, match='all'))
        self.execute_module(failed=True)
