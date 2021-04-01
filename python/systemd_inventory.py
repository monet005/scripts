#!/usr/bin/env python3

import requests
import logging
import json
import argparse


class ConsulHelper():
    """
    A collection of consul api methods
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
                logger.info('{} systemd config available in consul'
                            .format(service_name))
                return data
            else:
                logger.error('{} service does not have consul '
                             'systemd key-value entry'
                             .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))

    def get_all_services(self):
        try:
            r = requests.get('{}/services'.format(self.ctlg_url))
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
            r = requests.get('{}/service/{}'
                             .format(self.ctlg_url, service_name))
            if r.status_code == 200:
                items = r.json()
                nodes = [item.get('Node') for item in items]
                svc_node_map.update({service_name: nodes})
            else:
                logger.error('Error in getting data from consul')

        except Exception as e:
            logger.error('Unable to connect to {}: {}'.format(consul_url, e))

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
                    inv_svc_name = service_name.replace(' ', '_')
                    svc_key = 'systemd_{}'.format(inv_svc_name)
                    try:
                        status = item.get('ServiceMeta')['systemd']
                        if status:
                            # Convert string to boolean for consistency
                            if status.lower() == 'true':
                                status = True
                            elif status.lower() == 'false':
                                status = False
                            logger.info('{} systemd defined on {}'
                                        .format(service_name, node))
                            status_items.append({node: {svc_key: status}})
                        else:
                            logger.warning('{} systemd key is null on {}'
                                           .format(service_name, node))
                            status_items.append({node: {svc_key: False}})
                    except KeyError:
                        logger.warning('{} service json file on {} '
                                       'does not have systemd key'
                                       .format(service_name, node))
                        status_items.append({node: {svc_key: False}})
                status_map.update({service_name: status_items})
            else:
                logger.error('{} service does not exist in consul'
                             .format(service_name))
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))

        return status_map

    def get_all_nodes(self):
        try:
            r = requests.get('{}/nodes'.format(self.ctlg_url))
            if r.status_code == 200:
                items = r.json()
                nodes = [node.get('Node') for node in items]
            else:
                logger.warning('Error in getting data from consul')
        except Exception as e:
            logger.error('Error connecting to {}: {}'.format(consul_url, e))

        return nodes


class SystemdConfigCheck():
    def __init__(self, systemd_config, svc_name):
        self.systemd_config = systemd_config
        self.svc_name = svc_name
        self.reqd_params = ['User',
                            'ExecStart',
                            'ExecStop',
                            'After']

    def get_params(self):
        lines = self.systemd_config.split()
        results = {}
        for item in self.reqd_params:
            check = [i for i in lines if i.startswith(item)]
            if len(check) == 0:
                results.update({item: ''})
            else:
                v = check[0].split('=')
                results.update({v[0]: v[1]})
        return results

    def check_root_user(self):
        r = self.get_params()
        if r.get('User') == 'root':
            logger.warning('{} config check failed - root user defined'
                           .format(self.svc_name))
            return False
        else:
            logger.info('{} config check passed - non-root user defined'
                        .format(self.svc_name))
            return True

    def check_params(self):
        r = self.get_params()
        test_results = []
        for k, v in r.items():
            if v:
                logger.info('{} config check passed - {} param defined'
                            .format(self.svc_name, k))
                test_results.append(True)
            else:
                logger.warning('{} config check failed - {} param not defined'
                               .format(self.svc_name, k))
                test_results.append(False)

        if all(test_results):
            return True
        else:
            return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', help='Provide hostname')
    args = parser.parse_args()
    ch = ConsulHelper(consul_url)
    all_services = ch.get_all_services()
    nodes = ch.get_all_nodes()
    hostvars = {}
    hostvarlist = []
    inventory = {}

    # Systemd and ansible inventory file creation tasks
    for svc_name in all_services:
        svc_data = ch.get_systemd_config(svc_name)
        node_per_svc = ch.get_nodes_per_service(svc_name)
        # Replace service names with spaces with _
        inv_svc_name = svc_name.replace(' ', '_')
        inventory[inv_svc_name] = {'hosts': node_per_svc[svc_name]}

        if svc_data:
            systemd_check = SystemdConfigCheck(svc_data, svc_name)
            check_root = systemd_check.check_root_user()
            check_params = systemd_check.check_params()

            if check_root and check_params:
                inventory[inv_svc_name]['vars'] = {'systemd_conf_check_{}'
                                                   .format(inv_svc_name): True}
            else:
                logger.warning('{} config overall checks failed'
                               .format(svc_name))
                inventory[inv_svc_name]['vars'] = {'systemd_conf_check_{}'
                                                   .format(inv_svc_name):
                                                   False}
        else:
            inventory[inv_svc_name]['vars'] = {'systemd_conf_check_{}'
                                               .format(inv_svc_name): False}

        status_map = ch.get_systemd_status_per_node(svc_name)
        values = status_map.get(svc_name)

        for v in values:
            hostvarlist.append(v)

    for n in nodes:
        tmp = {}
        items = [i.get(n) for i in hostvarlist if i.get(n)]
        for item in items:
            tmp.update(item)
        hostvars[n] = tmp

    inventory['_meta'] = {'hostvars': hostvars}

    if args.list:
        print(json.dumps(inventory, indent=2))
    elif args.host:
        print(json.dumps(hostvars.get(args.host, {})))


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    consul_url = 'http://pi-1:8500'

    main()
