#!/usr/bin/env python3

import requests
import subprocess


def get_nodes_per_service(service_name, systemd_enabled='true'):
    r = requests.get('{}/service/{}'.format(catalog_url, service_name))
    items = r.json()
    nodes = []
    for item in items:
        try:
            systemd_meta = item.get('ServiceMeta')['systemd_enabled']
            if systemd_meta and systemd_meta == systemd_enabled:
                nodes.append(item.get('Node'))
        except KeyError:
            print('systemd_enabled key is not defined for {} service'
                  .format(service_name))

    return nodes


def get_services_all():
    r = requests.get('{}/services'.format(catalog_url))
    items = r.json()
    services = [item for item in items.keys()]
    return services


def create_template(src_template, dest_file):
    try:
        args = ['consul-template',
                '-template',
                '{}:{}'.format(src_template, dest_file),
                '--once']
        cmd = subprocess.run(args)
        cmd.check_returncode
    except Exception as e:
        print(e)



def main():
    all_services = get_services_all()
    for service in all_services:
        service_with_systemd = get_nodes_per_service(service)
        if service_with_systemd:
            create_template(service,
                            src_template='/home/raemone/consul_systemd/templates/systemd_template.tpl',
                            dest_file='/home/raemone/consul_systemd/output/{}.service'.format(service))


if __name__ == "__main__":
    catalog_url = 'http://pi-1:8500/v1/catalog'
    main()
