#!/usr/bin/env python

'''
script for taking os customization snapshot and compare its output
'''

import subprocess
import json
import os
import argparse

parser = argparse.ArgumentParser(description='tool to collect server customization details, also use this to compare the outputs of two servers')
parser_group = parser.add_mutually_exclusive_group(required=True)
parser_group.add_argument('-s', '--snap', action='store_true', help='take customization snapshot')
parser_group.add_argument('-c', '--compare', action='store', nargs=2, dest='file', help='specify file full path')
args = parser.parse_args()

# modules here
def sysctl():
    proc = subprocess.Popen(["sysctl", "-a"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    sys_list = [ tuple(line.split(' = ')) for line in out if line ]
    sys_dict = dict(sys_list)
    return { 'sysctl': sys_dict }

def groups():
    proc = subprocess.Popen(["cat", "/etc/group"], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    groups_dict = {}
    for line in out:
        if line:
            item = line.split(':')
            group_dict = { item[0]: {'gid': item[2], 'members': item[3]}}
            groups_dict.update(group_dict)

    return { 'groups': groups_dict }

def sgroups(user):
    proc = subprocess.Popen(["groups", user], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    sgroups_raw = out[0].split(' : ')[1].split()
    # comma separated list of secondary groups, primary group excluded
    sgroups = ','.join(sgroups_raw[1:])

    return sgroups

def users():
    proc = subprocess.Popen(["cat", "/etc/passwd"], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    # convert gid numerical value to groupname
    groups_data = groups()
    groups_values = groups_data.values()
    groups_dict = {}
    for item in groups_values:
        groups_dict.update(item)

    users_dict = {}
    for line in out:
        if line:
            item = line.split(':')
            user_dict = {item[0]: {'uid': item[2], 'gid': item[3], \
                        'gecos': item[4], 'homedir': item[5], 'shell': item[6] }}
            users_dict.update(user_dict)

    mapped = users_dict
    for u_item in users_dict.keys():
        for g_item in groups_dict.keys():
            if users_dict[u_item]['gid'] == groups_dict[g_item]['gid']:
                mapped[u_item]['groupname'] = g_item

    # add secondary groups to users_dict
    for u_item in users_dict.keys():
        mapped[u_item]['secondary_groups'] = sgroups(u_item)

    return { 'users': mapped }

def rpm():
    proc = subprocess.Popen(["rpm", "-qa", "--queryformat", "%{NAME}\n"], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    return { 'rpm': out[:-1] }

def df(mountpt):
    proc = subprocess.Popen(["df", "-hP", mountpt], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    line = out[1].split()
    return line[1]

def mounts():
    proc = subprocess.Popen(["cat", "/proc/mounts"], stdout=subprocess.PIPE)
    data = proc.communicate()
    out = data[0].split('\n')

    mount_dict = {}
    exclude = ['binfmt_misc', 'configfs', 'debugfs', 'devpts', 'devtmpfs', \
               'hugetlbfs', 'mqueue', 'proc', 'pstore', 'securityfs', 'selinuxfs', \
               'sunrpc', 'sysfs', 'systemd-1', 'vagrant', 'cgroup', 'tmpfs', 'rootfs', 'none' ]

    for line in out:
        if line:
        #['/dev/mapper/centos-root', '/', 'xfs', 'rw,seclabel,relatime,attr2,inode64,noquota', '0', '0']
            l = line.split()
            if l[0] not in exclude:
                mount_dict.update({ l[1]: { 'size': df(l[0]), 'device': l[0], 'fstype': l[2], 'mount_opts': l[3] }})
    
    return { 'mounts': mount_dict }


# Compare func here
def compare(keyname, a, b):
    delta = {}
    print("[{0} checks]".format(keyname))

    try:
        common_keys = filter(b.has_key, a.keys())
        diff_keys = a.viewkeys() - b.viewkeys()
        diff_list = list(diff_keys)
        count = len(diff_list)
        for key in common_keys:
            if a[key] != b[key]:
                print("(a) {0}: {1}\n(b) {2}: {3}\n".format(key, a[key], key, b[key]))
                delta.update({key: a[key]})

        if len(diff_list) != 0:
            print("{0} items not on (b): {1}\n".format(count, diff_list))
            for diff_key in diff_list:
                delta.update({diff_key: a[diff_key]})

    except AttributeError:
        diff_a2b = list(set(a) - set(b))
        count = len(diff_a2b)
        print("{0} items not on (b): {1}\n".format(count, diff_a2b))
        delta.update({keyname: diff_a2b})

    return delta

# main
def main():
    all = {}
    module_functions = [groups(), users(), sysctl(), rpm(), mounts()]
    modules = ['groups', 'users', 'sysctl', 'rpm', 'mounts']
    hostname = os.uname()[1]

    if args.snap:
        for module in module_functions:
            all.update(module)

        with open(hostname + '.json', 'w') as f:
            x = json.dumps(all, indent=4)
            f.write(x)
            print("output: {0}".format(f.name))

    if args.file:
        f = args.file
        try:
            #with open(f[0], 'r') as a, open(f[1], 'r') as b:
            
            with open(f[0], 'r') as a:
                a_data = json.load(a)
            
            with open(f[1], 'r') as b:
                b_data = json.load(b)

        except IOError as e:
            exit(e)

    # compare & create json of deltas based on a values
        print("compare a to b")
        print("-" * 60)
        print("a: {0}\t b: {1}".format(f[0], f[1]))
        print("-" * 60)

        all_delta = {}
        for m in modules:
            run_module = compare(m, a_data[m], b_data[m])
            run_module
            if m == 'rpm':
                all_delta.update(run_module)
            else:
                all_delta.update({m: run_module})

        with open('delta.json', 'w') as f:
            x = json.dumps(all_delta, indent=4)
            f.write(x)
            print("delta output: {0}".format(f.name))
            

if __name__ == "__main__": 
   main()












