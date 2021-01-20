#!/usr/bin/env python3

import requests
import logging
import sys


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

consul_url = 'http://pi-1:8500'


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
                return data
            else:
                logger.warning('{} does not exist in consul key-value store'
                               .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}'.format(consul_url))
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
            logger.error('Error connecting to {}'.format(consul_url))
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
            logger.error('Error connecting to {}'.format(consul_url))
            sys.exit(1)

        return svc_node_map

    def get_systemd_status_per_node(self, service_name):
        status_map = {}
        try:
            print('{}/service/{}'
                  .format(self.ctlg_url, service_name))
            r = requests.get('{}/service/{}'
                             .format(self.ctlg_url, service_name))
            print(r.status_code)
            items = r.json()
            if items:
                status_items = []
                for item in items:
                    status = item.get('ServiceMeta')['systemd_enabled']
                    node = item.get('Node')
                    status_items.append({'node': node,
                                         'systemd_enabled': status})
                status_map.update({service_name: status_items})
            else:
                logger.warning('{} service does not exist in consul'
                               .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}'.format(consul_url))
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

    a = ch.get_all_nodes()
    b = ch.get_systemd_status_per_node('jenkins')
    print(b)







if __name__ == "__main__":
    main()


   


