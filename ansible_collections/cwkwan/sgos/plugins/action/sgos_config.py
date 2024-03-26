#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action.network import ActionModule as ActionNetworkModule


class ActionModule(ActionNetworkModule):

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        self._config_module = True
        return super(ActionModule, self).run(task_vars=task_vars)

