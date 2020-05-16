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

def run(*args):
    cmd = list(args)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc_data = proc.communicate()
    value = proc_data[0].split('\n')

    return value

# modules here
def sysctl():
    out = run("sysctl", "-a")
    sys_list = [ tuple(line.split(' = ')) for line in out if line ]
    sys_dict = dict(sys_list)
    return { 'sysctl': sys_dict }

def groups():
    out = run("cat", "/etc/group")
    groups_dict = {}
    for line in out:
        if line:
            item = line.split(':')
            group_dict = { item[0]: {'gid': item[2], 'members': item[3]}}
            groups_dict.update(group_dict)

    return { 'groups': groups_dict }

def sgroups(user):
    out = run("groups", user)
    sgroups_raw = out[0].split(' : ')[1].split()
    # comma separated list of secondary groups, primary group excluded
    sgroups = ','.join(sgroups_raw[1:])

    return sgroups

def users():
    out = run("cat", "/etc/passwd")
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
    out = run("rpm", "-qa", "--queryformat", "%{NAME}\n")
    return { 'rpm': out[:-1] }

def df(mountpt):
    out = run("df", "-hP", mountpt)
    line = out[1].split()
    return line[1]

def mounts():
    out = run("cat", "/proc/mounts")
    mount_dict = {}
    exclude = ['binfmt_misc', 'configfs', 'debugfs', 'devpts', 'devtmpfs', \
               'hugetlbfs', 'mqueue', 'proc', 'pstore', 'securityfs', 'selinuxfs', \
               'sunrpc', 'sysfs', 'systemd-1', 'vagrant', 'cgroup', 'tmpfs', 'rootfs', \
               'none', 'nfsd', 'fusectl' ]

    for line in out:
        if line:
            l = line.split()
            if l[0] not in exclude:
                mount_dict.update({ l[1]: { 'size': df(l[1]), 'device': l[0], 'fstype': l[2], 'mount_opts': l[3] }})
    
    return { 'mounts': mount_dict }

def network():
    out = run("ip","-4","-o","addr")

    net_dict = {}
    for line in out:
        if line:
            l = line.split()
            net_dict.update({l[1]: {'ip_addr': l[3]}})
            ether = '/sys/class/net/' + l[1] + '/address'
            state = '/sys/class/net/' + l[1] + '/operstate'
            with open(ether, 'r') as f:
                net_dict[l[1]]['mac_address'] = f.read().rstrip()

            with open(state, 'r') as f:
                net_dict[l[1]]['status'] = f.read().rstrip()

    return {'network': net_dict}

def disks():
    out = run("lsblk", "-l", "-n", "-o", "name,size,type")
    disks_dict = {}
    for line in out:
        if line:
            l = line.split()
            if l[2] == 'disk':
                disks_dict.update({l[0]: l[1]})
    
    return {'disks': disks_dict}

# Compare func here
def compare(keyname, a, b):
    delta = {}
    print("[{0} check]".format(keyname))

    try:
        common_keys = filter(b.has_key, a.keys())
        for key in common_keys:
            if a[key] != b[key]:
                print("(a) {0}: {1}\n(b) {2}: {3}\n".format(key, a[key], key, b[key]))
                delta.update({key: a[key]})
  
        diff_keys = a.viewkeys() - b.viewkeys()
        diff_list = list(diff_keys)
        count = len(diff_list)

        if len(diff_list) != 0:
            print("{0} item(s) not on (b): {1}\n".format(count, diff_list))
            for diff_key in diff_list:
                delta.update({diff_key: a[diff_key]})

    except AttributeError:
        diff_a2b = list(set(a) - set(b))
        count = len(diff_a2b)
        print("{0} item(s) not on (b): {1}\n".format(count, diff_a2b))
        delta.update({keyname: diff_a2b})

    return delta

# main
def main():
    all = {}
    module_functions = [groups(), users(), sysctl(), rpm(), mounts(), network(), disks()]
    modules = ['groups', 'users', 'sysctl', 'rpm', 'mounts', 'network', 'disks']
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
            with open(f[0], 'r') as a:
                a_data = json.load(a)
            
            with open(f[1], 'r') as b:
                b_data = json.load(b)

        except IOError as e:
            exit(e)

    # compare & create json of deltas based on A values
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
            print("\ndelta output: {0}".format(f.name))
            
if __name__ == "__main__": 
   main()












