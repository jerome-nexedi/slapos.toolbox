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



def main(sr_directory, partition_list):

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
                    if not created(partition_path):
                        create(sr_directory, partition_path,
                               slapcontainer_conf)
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



def created(partition_path):
    # XXX: Hardcoded
    should_exists = ['config', 'rootfs']
    return all((os.path.exists(os.path.join(partition_path, f))
                for f in should_exists))



def create(sr_directory, partition_path, conf):
    lxc_debian = os.path.join(sr_directory,
                              'parts/lxc/lib/lxc/templates/lxc-debian')
    call([lxc_debian, '-p', partition_path])

    lxc_filename = os.path.join(partition_path, 'config')
    lxc = LXCConfig(lxc_filename)
    lxc.utsname = os.path.basename(partition_path)
    lxc.network.type = 'vlan'
    lxc.network.link = conf.get('information', 'interface')
    lxc.network.name = 'eth0'
    # XXX: Hardcoded netmasks
    lxc.network.ipv4 = '%s/32' % conf.get('information', 'ipv4')
    lxc.network.ipv6 = '%s/128' % conf.get('information', 'ipv6')
    lxc.network.flags = 'up'

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



def call(command_line):
    # for debug :
    # print ' '.join(command_line)
    process = subprocess.Popen(command_line, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE)
    process.stdin.flush()
    process.stdin.close()

    if process.wait() != 0:
        raise SlapContainerError("Subprocess call failed")

    out = process.stdout.read()
    # for debug :
    # print out
    return out
