#!/usr/bin/env python3

import requests
import logging
import sys
import os


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

consul_url = 'http://pi-1:8500'
systemd_dirname = 'sabre_systemd'


class ConsulHelper():
    """
    A collection of consul helper functions
    """

    def __init__(self, consul_url):
        self.consul_url = consul_url
        self.kv_url = '{}/v1/kv'.format(consul_url)
        self.ctlg_url = '{}/v1/catalog'.format(consul_url)

    def get_systemd_config(self, service_name):
        try:
            r = requests.get('{}/systemd/{}?raw'
                             .format(self.kv_url, service_name))
            if r.status_code == 200:
                data = r.text
                logger.info('{} systemd config download OK'
                            .format(service_name))
                return data
            else:
                logger.warning('{} service does not have consul '
                               'systemd key-value entry'
                               .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))
            sys.exit(1)

    def get_all_services(self):
        try:
            r = requests.get('{}/services'.format(self.ctlg_url))
            if r.status_code == 200:
                items = r.json()
                services = [item for item in items.keys()]
            else:
                logger.warning('Error in getting data from consul')
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))
            sys.exit(1)

        return services

    def get_nodes_per_service(self, service_name):
        svc_node_map = {}
        try:
            r = requests.get('{}/service/{}'
                             .format(self.ctlg_url, service_name))
            if r.status_code == 200:
                items = r.json()
                nodes = [item.get('Node') for item in items]
                svc_node_map.update({service_name: nodes})
            else:
                logger.warning('Error in getting data from consul')

        except Exception as e:
            logger.error('Unable to connect to {}: {}'.format(consul_url, e))
            sys.exit(1)

        return svc_node_map

    def get_systemd_status_per_node(self, service_name):
        status_map = {}
        try:
            r = requests.get('{}/service/{}'
                             .format(self.ctlg_url, service_name))
            items = r.json()
            if items:
                status_items = []
                for item in items:
                    node = item.get('Node')
                    try:
                        status = item.get('ServiceMeta')['systemd_enabled']
                        if status:
                            status_items.append({'node': node,
                                                 'systemd_enabled': status})
                        else:
                            logger.warning('{} - systemd_enabled key is null'
                                           .format(service_name))
                    except KeyError:
                        logger.warning('{} service json file on {} '
                                       'does not have systemd_enabled key'
                                       .format(service_name, node))
                status_map.update({service_name: status_items})
            else:
                logger.warning('{} service does not exist in consul'
                               .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url))
            sys.exit(1)

        return status_map

    def get_all_nodes(self):
        all = {}
        all_services = self.get_all_services()
        for service in all_services:
            s = self.get_systemd_status_per_node(service)
            all.update(s)

        return all


def main():
    ch = ConsulHelper(consul_url)
    all_services = ch.get_all_services()

    # Systemd and ansible inventory file creation tasks
    try:
        os.mkdir(systemd_dirname)
    except Exception as e:
        logger.warning('Unable to create {} directory: {}'
                       .format(systemd_dirname, e))

    try:
        os.remove('systemd_enabled_hosts')
        logger.info('systemd_enabled_hosts cleared')
    except Exception as e:
        logger.error('Unable to delete systemd_enabled_hosts: {}'
                     .format(e))

    for svc_name in all_services:
        svc_data = ch.get_systemd_config(svc_name)
        if svc_data:
            dest = '{}/{}.service'.format(systemd_dirname, svc_name)
            with open(dest, 'w') as f:
                f.write(svc_data)
                logger.info('{} systemd template created'.format(dest))

            svc_status_map = ch.get_systemd_status_per_node(svc_name)

            with open('systemd_enabled_hosts', 'a') as f:
                if svc_status_map.get(svc_name):
                    f.write('\n')
                    f.write('[{}]\n'.format(svc_name))

                    values = svc_status_map.get(svc_name)
                    for v in values:
                        if v.get('systemd_enabled') == 'true':
                            f.write('{}\n'.format(v.get('node')))
                            


if __name__ == "__main__":
    main()
