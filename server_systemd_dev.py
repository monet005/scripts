#!/usr/bin/env python3

import requests
import logging
import sys
import os
import git


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
                logger.info('{} systemd config available'
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
                        status = item.get('ServiceMeta')['systemd']
                        if status:
                            status_items.append({'node': node,
                                                 'systemd': status})
                        else:
                            logger.warning('{} - systemd key is null'
                                           .format(service_name))
                    except KeyError:
                        logger.warning('{} service json file on {} '
                                       'does not have systemd key'
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


class Git():
    """
    To do git operations
    """
    def __init__(self, repodir, repo_src):
        self.repodir = repodir
        self.repo_src = repo_src

    def check_repodir(self):
        check = os.path.isdir(self.repodir)
        if check:
            logger.info('{} git repodir already exists'.format(self.repodir))
        else:
            os.mkdir(self.repodir)
            logger.info('{} repodir created'.format(self.repodir))

    def update_gitrepo(self):
        try:
            repo = git.Repo(repodir)
            if repo.is_dirty(untracked_files=True):
                logger.info('Git repo changes detected')
                repo.git.add('--all')
                repo.git.commit(m='added files')
                repo.remotes.origin.push()
                logger.info('Pushed changes to {}'.format(repo_src))
            else:
                logger.info('No git repo changes detected on {}'
                            .format(repodir))
        except git.exc.InvalidGitRepositoryError:
            logger.info('Cloning {} repo'.format(repo.src))
            git.Repo.clone_from(repo_src, repodir)


class SystemdCheck():
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
            logger.error('{} config check failed - root user defined'
                         .format(self.svc_name))
            return False
        else:
            logger.info('{} config check OK - non-root user defined'
                        .format(self.svc_name))
            return True

    def check_params(self):
        r = self.get_params()
        for k, v in r.items():
            if v:
                logger.info('{} config check OK - {} param defined'
                            .format(self.svc_name, k))
                return True
            else:
                logger.info('{} config check failed - {} param not configured'
                            .format(self.svc_name, k))
                return False


def main():
    ch = ConsulHelper(consul_url)
    all_services = ch.get_all_services()

    # Systemd and ansible inventory file creation tasks
    try:
        if os.path.isdir(filesdir):
            logger.info('{} dir already exists'.format(filesdir))
        else:
            os.makedirs(filesdir)
            logger.info('{} dir created'.format(filesdir))
    except Exception as e:
        logger.warning('Unable to create {} directory: {}'
                       .format(filesdir, e))

    try:
        if os.path.exists(ansible_inv):
            os.remove(ansible_inv)
            logger.info('systemd_hosts cleared')
    except Exception as e:
        logger.warning('Unable to delete systemd_hosts: {}'
                       .format(e))

    for svc_name in all_services:
        svc_data = ch.get_systemd_config(svc_name)

        if svc_data:
            systemd_check = SystemdCheck(svc_data, svc_name)
            check_root = systemd_check.check_root_user()
            check_params = systemd_check.check_params()
            dest = os.path.join(filesdir, '{}.service'
                                .format(svc_name))

            if check_root and check_params:
                with open(dest, 'w') as f:
                    f.write(svc_data)
                    logger.info('{} systemd template created'.format(dest))

                svc_status_map = ch.get_systemd_status_per_node(svc_name)
                with open(ansible_inv, 'a') as f:
                    if svc_status_map.get(svc_name):
                        f.write('\n')
                        f.write('[{}]\n'.format(svc_name))
                        logger.info('{} ansible inventory file created'
                                    .format(ansible_inv))

                        values = svc_status_map.get(svc_name)
                        for v in values:
                            status = v.get('systemd')
                            node = v.get('node')
                            f.write('{}\t systemd={}\n'
                                    .format(node, status))
            else:
                logger.error('{} config check failed, '
                             'excluding from template and inventory creation'
                             .format(svc_name))

    # Bitbucket repo tasks
    gt = Git(repodir, repo_src)
    gt.check_repodir()
    gt.update_gitrepo()


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    consul_url = 'http://pi-1:8500'
    basedir = 'sabre_systemd'
    filesdir = os.path.join(basedir, 'sabre_systemd', 'files')
    ansible_inv = os.path.join(basedir, 'sabre_systemd_hosts')
    repodir = 'sabre_systemd'
    repo_src = 'git@github.com:monet005/sabre_systemd.git'

    main()
