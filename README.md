## Environment

- Ansible 2.9.1
- Bluecoat ProxySG SGOS v6.7.x

## Custom network_cli

This requires using the included `sgos_network_cli.py` as connection plugin instead of the default one. By specifying `connection_plugins` in ansible.cfg

```ini
[defaults]:
connection_plugins = /ansible-galaxy-sgos-collection/plugins/connection
```