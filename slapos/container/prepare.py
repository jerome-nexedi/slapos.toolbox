# -*- coding: utf-8 -*-

import ConfigParser
import os
import subprocess

import lockfile

from .config import LXCConfig

class SlapContainerError(Exception):
    """This exception is thrown, if there is
    any failure during slapcontainer preparation,
    starting or stopping process"""



def main(sr_directory, partition_list, bridge_name):

    for partition_path in partition_list:
        slapcontainer_filename = os.path.join(partition_path,
                                              '.slapcontainer')
        if os.path.isfile(slapcontainer_filename):
            lock = lockfile.FileLock(slapcontainer_filename)
            lock.acquire(timeout=0)
            slapcontainer_conf = ConfigParser.ConfigParser()
            slapcontainer_conf.read(slapcontainer_filename)
            try:

                requested_status = slapcontainer_conf.get('requested',
                                                          'status')

                if requested_status == 'started':
                    create(sr_directory, partition_path,
                           slapcontainer_conf, bridge_name)
                    if status(sr_directory, partition_path) == 'stopped':
                        start(sr_directory, partition_path)
                else:
                    if status(sr_directory, partition_path) == 'started':
                        stop(sr_directory, partition_path)
            except lockfile.LockTimeout:
                # Can't do anything, we'll see on the next run
                pass
            finally:
                lock.release()



def start(sr_directory, partition_path):
    lxc_start = os.path.join(sr_directory,
                             'parts/lxc/bin/lxc-start')
    config_filename = os.path.join(partition_path, 'config')

    call([lxc_start, '-f', config_filename,
          '-n', os.path.basename(partition_path),
          '-d'])



def stop(sr_directory, partition_path):

    # TODO : Check if container is stopped
    #        Stop container
    pass



def create(sr_directory, partition_path, conf, bridge_name):
    lxc_filename = conf.get('config', 'file')
    lxc = LXCConfig()
    lxc.utsname = conf.get('requested', 'name')
    lxc.network.type = 'veth'
    lxc.network.link = bridge_name
    lxc.network.veth.pair = 'lxc%s' % conf.get('network', 'interface')
    lxc.network.name = 'eth0'
    lxc.network.flags = 'up'
    # XXX: Hardcoded stuff
    lxc.tty = '4'
    lxc.pts = '1024'
    lxc.cgroup.devices.deny = 'a'
    lxc.cgroup.devices.allow = [
        'c 1:3 rwm',
        'c 1:5 rwm',
        'c 5:1 rwm',
        'c 5:0 rwm',
        'c 4:0 rwm',
        'c 4:1 rwm',
        'c 1:9 rwm',
        'c 1:8 rwm',
        'c 136:* rwm',
        'c 5:2 rwm',
        'c 254:0 rwm',
    ]
    # XXX : This is a relic of previous code, even if it is versionned
    #       this could be usefull in future
    # lxc.mount.entry = [
    #     'proc %s proc nodev,noexec,nosuid 0 0' % os.path.join(rootfs_dir, 'proc'),
    #     'sysfs %s sysfs defaults 0 0' % os.path.join(rootfs_dir, 'sys'),
    # ]
    lxc.rootfs = conf.get('rootfs', 'image')

    with open(lxc_filename, 'w') as lxc_file:
        lxc_file.write(str(lxc))



def destroy(partition_path):
    # TODO: Destroy container
    pass



def status(sr_directory, partition_path):
    lxc_info = call([os.path.join(sr_directory, 'parts/lxc/bin/lxc-info'),
                     '-n', os.path.basename(partition_path)])
    if 'RUNNING' in lxc_info:
        return 'started'
    else:
        return 'stopped'



def call(command_line, override_environ={}):
    # for debug :
    # print ' '.join(command_line)
    environ = dict(os.environ)
    environ.update(override_environ)
    process = subprocess.Popen(command_line, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, env=environ)
    process.stdin.flush()
    process.stdin.close()

    if process.wait() != 0:
        raise SlapContainerError("Subprocess call failed")

    out = process.stdout.read()
    # for debug :
    # print out
    return out
