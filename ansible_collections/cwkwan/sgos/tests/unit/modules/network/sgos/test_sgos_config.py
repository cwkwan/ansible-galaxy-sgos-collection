#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from unittest.mock import patch
from ansible_collections.cwkwan.sgos.plugins.modules import sgos_config
from sgos_module import TestSgosModule, load_fixture, set_module_args


class TestSgosConfigModule(TestSgosModule):

    module = sgos_config

    def setUp(self):
        super(TestSgosConfigModule, self).setUp()

        self.mock_load_config = patch('ansible_collections.cwkwan.sgos.plugins.modules.sgos_config.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestSgosConfigModule, self).tearDown()
        self.mock_load_config.stop()

    def test_sgos_config_src(self):
        src = load_fixture('sgos_config_src.cfg')
        set_module_args(dict(src=src))
        commands = ['appliance-name foo']
        self.execute_module(changed=True, commands=commands)

    def test_sgos_config_lines(self):
        set_module_args(dict(lines=['appliance-name foo']))
        commands = ['appliance-name foo']
        self.execute_module(changed=True, commands=commands)

    def test_sgos_config_src_and_lines_fails(self):
        args = dict(src='foo', lines='foo')
        set_module_args(args)
        self.execute_module(failed=True)
