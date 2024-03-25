#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import json
import unittest

from os import path
from unittest.mock import MagicMock, call
from ansible.module_utils._text import to_bytes
from ansible_collections.cwkwan.sgos.plugins.cliconf import sgos

FIXTURE_DIR = b'%s/fixtures/sgos' % (
    path.dirname(path.abspath(__file__)).encode('utf-8')
)


def _connection_side_effect(*args, **kwargs):
    try:
        if args:
            value = args[0]
        else:
            value = kwargs.get('command')

        value = value.replace(b'/', b' ')
        fixture_path = path.abspath(
            b'%s/%s' % (FIXTURE_DIR, b'_'.join(value.split(b' ')))
        )
        with open(fixture_path, 'rb') as file_desc:
            return file_desc.read()
    except (OSError, IOError):
        if args:
            value = args[0]
            return value
        elif kwargs.get('command'):
            value = kwargs.get('command')
            return value

        return 'Nope'


class TestPluginCLIConfSGOS(unittest.TestCase):
    """ Test class for SGOS CLI Conf Methods
    """
    def setUp(self):
        self._mock_connection = MagicMock()
        self._mock_connection.send.side_effect = _connection_side_effect
        self._cliconf = sgos.Cliconf(self._mock_connection)
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_get_device_info(self):
        """ Test get_device_info
        """
        device_info = self._cliconf.get_device_info()

        mock_device_info = {
            'network_os': 'sgos',
            'network_os_hostname': 'testdevice01',
            'network_os_model': 'S200-20',
            'network_os_version': 'SGOS 6.7.4.144 Proxy Edition'
        }

        self.assertEqual(device_info, mock_device_info)

    def test_get_capabilities(self):
        """ Test get_capabilities
        """
        capabilities = json.loads(self._cliconf.get_capabilities())
        mock_capabilities = {
            'network_api': 'cliconf',
            'rpc': [
                'get_config',
                'edit_config',
                'get_capabilities',
                'get',
                'enable_response_logging',
                'disable_response_logging'
            ],
            'device_info': {
                'network_os': 'sgos',
                'network_os_hostname': 'testdevice01',
                'network_os_model': 'S200-20',
                'network_os_version': 'SGOS 6.7.4.144 Proxy Edition'
            }
        }

        self.assertEqual(
            mock_capabilities,
            capabilities
        )
