#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from unittest.mock import patch
from ansible_collections.cwkwan.sgos.plugins.modules import sgos_facts
from sgos_module import TestSgosModule, load_fixture, set_module_args


class TestSgosFactsModule(TestSgosModule):

    module = sgos_facts

    def setUp(self):
        super(TestSgosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible_collections.cwkwan.sgos.plugins.modules.sgos_facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestSgosFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = args[1]
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_').replace('/', '~')
                output.append(load_fixture('sgos_facts_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_sgos_facts(self):
        set_module_args(dict(gather_subset='default'))
        result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'S200-20'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], '1234567890'
        )

