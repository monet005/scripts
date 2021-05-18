#!/usr/bin/env python3

import requests
import logging
import json
import argparse


class ConsulApi():
    """
    A collection of consul api methods
    """

    def __init__(self, consul_url):
        self.consul_url = consul_url
        self.kv_url = '{}/v1/kv'.format(consul_url)
        self.catalog_url = '{}/v1/catalog'.format(consul_url)
        self.service_url = '{}/service'.format(self.catalog_url)
        self.node_url = '{}/node'.format(self.catalog_url)

    def get_all_services(self):
        try:
            r = requests.get('{}/services'.format(self.catalog_url))
            if r.status_code == 200:
                items = r.json()
                services = [item for item in items.keys()]
            else:
                logger.error('Error in getting data from consul')
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))

        return services

    def get_nodes_per_service(self, service_name):
        svc_node_map = {}
        try:
            r = requests.get('{}/{}'.format(self.service_url, service_name))
            if r.status_code == 200:
                items = r.json()
                nodes = [item.get('Node') for item in items]
                svc_node_map.update({service_name: nodes})
            else:
                logger.error('Error in getting data from consul')

        except Exception as e:
            logger.error('Unable to connect to {}: {}'.format(consul_url, e))

        return svc_node_map

    def get_node_ip_address(self, node):
        try:
            r = requests.get('{}/{}'.format(self.node_url, node))
            if r.status_code == 200:
                items = r.json()
                return items.get('Node').get('Address')
        except Exception as e:
            logger.error('Unable to connect to {}: {}'.format(consul_url, e))


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', help='Provide hostname')
    args = parser.parse_args()
    consul_url = 'http://pi-0:8500'
    consul_instance = ConsulApi(consul_url)
    services = consul_instance.get_all_services()
    inventory = {}
    hostvars = {}

    for service in services:
        nodes_per_service = consul_instance.get_nodes_per_service(service)
        nodes = nodes_per_service[service]
        inventory[service] = {'hosts': nodes}
        for node in nodes:
            hostvars[node] = {'ansible_ssh_host':
                              consul_instance.get_node_ip_address(node)}

    inventory['_meta'] = hostvars

    if args.list:
        print(json.dumps(inventory, indent=2))
    if args.host:
        print(json.dumps(hostvars[args.host], indent=2))
