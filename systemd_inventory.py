#!/usr/bin/env python3
"""
Script to generate dynamic ansible inventory from consul.
"""

import requests
import argparse
import json

baseurl = 'http://pi-1:8500/v1'
ctlog_url = '{}/catalog'.format(baseurl)
svcs_url = '{}/services'.format(ctlog_url)
svc_url = '{}/service'.format(ctlog_url)
kv_url = '{}/kv'.format(baseurl)


def get_data(src):
    try:
        r = requests.get(src)
        if r.status_code == 200:
            items = r.json()
            return items
        else:
            print('Unable to get data from consul')
    except Exception as e:
        print('Unable to connect to {}: '.format(e))


def check_systemd_config(svc_name):
    required_fields = ['User',
                       'ExecStart',
                       'ExecStop',
                       'After']

    try:
        r = requests.get('{}/systemd/{}?raw'.format(kv_url, svc_name))
        if r.status_code == 200:
            d = r.text
            lines = d.split()
            results = {}

            for item in required_fields:
                check = [i for i in lines if i.startswith(item)]
                if len(check) == 0:
                    results.update({item: ''})
                else:
                    v = check[0].split('=')
                    results.update({v[0]: v[1]})

            valid = 0
            for field in required_fields:
                check = results.get(field)

                if check:
                    valid += 0
                else:
                    valid += 1

                if results.get('User') == 'root':
                    valid += 1

                if valid == 0:
                    return {'systemd_check': 'passed'}
                elif valid == 1:
                    return {'systemd_check': 'failed'}
        else:
            return {'systemd_check': 'null'}

    except Exception as e:
        print('Unable to connect to consul: {}'.format(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--host', help='Provide hostname')
    args = parser.parse_args()
    svcs_data = get_data(svcs_url)

    # Also change the service names with spaces to '-'
    services = [item.replace(' ', '-') for item in svcs_data.keys()]
    inventory = {}
    node_items = {}
    grp_items = {}

    for service in services:
        sdata = get_data('{}/{}'.format(svc_url, service))
        nodes = [n.get('Node') for n in sdata]
        for s in sdata:
            try:
                node = s.get('Node')
                systemd_meta = s.get('ServiceMeta')['systemd']
                node_items.update({node: {'systemd': systemd_meta}})
            except KeyError:
                pass

        grp_items.update({service: {
                        'hosts': nodes,
                        'vars': {'systemd_filename':
                                 '{}.service'.format(service)}}})

        check = check_systemd_config(service)
        grp_var = grp_items[service]['vars']
        grp_var.update(check)
        grp_items.update(grp_var)

    if args.list:
        inventory.update(grp_items)
        inventory['_meta'] = {'hostvars': node_items}
        print(json.dumps(inventory, indent=4))
    elif args.host:
        print(node_items.get(args.host))


if __name__ == "__main__":
    main()
