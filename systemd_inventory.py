#!/usr/bin/env python3

import requests
import json

baseurl = 'http://pi-1:8500/v1'
ctlog_url = '{}/catalog'.format(baseurl)
svcs_url = '{}/services'.format(ctlog_url)
svc_url = '{}/service'.format(ctlog_url)
nodes_url = '{}/nodes'.format(ctlog_url)


def get_data(src):
    try:
        r = requests.get(src)
        if r.status_code == 200:
            items = r.json()
            return items
        else:
            print('Unable to get data')
    except Exception as e:
        print(e)


def main():
    node_data = get_data(nodes_url)
    svcs_data = get_data(svcs_url)
    services = [item for item in svcs_data.keys()]

    inv = {}
    for service in services:
        s = get_data('{}/{}'.format(svc_url, service))
        nodes = [item.get('Node') for item in node_data]

        inv.update({service: {
                    'hosts': nodes,
                    'vars': {'systemd_file': '{}.service'.format(service)}}})


    
    print(inv)







main()
