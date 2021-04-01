#!/usr/bin/env python3

import requests
from jinja2 import Template


class Systemd():
    """
    Creates a service's systemd definition based from Consul data.
    """

    def __init__(self, service_name, kv_baseurl, ctlg_baseurl):
        self.service_name = service_name
        self.kv_baseurl = kv_baseurl
        self.ctlg_baseurl = ctlg_baseurl

    def get_nodes(self, systemd_enabled='true'):
        """
        Get nodes that belong to a service with systemd enabled.
        """

        r = requests.get('{}/service/{}'
                         .format(self.ctlg_baseurl, self.service_name))
        items = r.json()
        nodes = []
        for item in items:
            try:
                systemd_meta = item.get('ServiceMeta')['systemd_enabled']
                if systemd_meta:
                    if systemd_meta == systemd_enabled:
                        nodes.append(item.get('Node'))
            except KeyError:
                print('{} - systemd_enabled key is not defined'
                      .format(self.service_name))

        return nodes

    def render_template(self):
        systemd_params = ['User',
                          'ExecStart',
                          'ExecStop']

        consul_data = {}
        for param in systemd_params:
            try:
                r = requests.get('{}/systemd/{}.service/{}?raw'
                                 .format(self.kv_baseurl,
                                         self.service_name,
                                         param))
                output = r.text
                consul_data.update({param: output})
            except Exception as e:
                print('Error in getting consul data')

        template = ("[Unit]\n"
                    "Description={{ service_name }} auto-start service\n"
                    "After=network.target\n"
                    "\n"
                    "[Service]\n"
                    "Type=simple\n"
                    "User={{ username }}\n"
                    "ExecStart={{ startcmd }}\n"
                    "ExecStop={{ stopcmd }}\n"
                    "\n"
                    "[Install]\n"
                    "WantedBy=multi-user.target\n")

        tm = Template(template)
        stm = tm.render(service_name=self.service_name,
                        username=consul_data.get('User'),
                        startcmd=consul_data.get('ExecStart'),
                        stopcmd=consul_data.get('ExecStop'))

        return stm


if __name__ == "__main__":
    ctlg_baseurl = 'http://pi-1:8500/v1/catalog'
    kv_baseurl = 'http://pi-1:8500/v1/kv'
    svc = Systemd('consul', kv_baseurl, ctlg_baseurl)
    y = svc.get_nodes()
    m = svc.render_template()
    print(y)
    with open('systemd_out', 'w') as f:
        f.write(m)


