# -*- coding: utf-8 -*-

import os
import subprocess
import logging

class SlapContainerError(Exception):
    """This exception is thrown, if there is
    any failure during slapcontainer preparation,
    starting or stopping process"""



def main(sr_directory, partition_list):

    logger = logging.getLogger('process')

    to_start = set()
    logger.debug('Processing partitions...')
    for partition_path in partition_list:
        partition_logger = logger.getChild(
            os.path.basename(partition_path)
        )
        partition_logger.debug('Processing...')

        # XXX: Hardcoded path
        slapcontainer_filename = os.path.join(partition_path,
                                              '.slapcontainername')
        if os.path.isfile(slapcontainer_filename):
            partition_logger.debug('Container found...')
            with open(slapcontainer_filename, 'r') as slapcontainer_file:
                name = slapcontainer_file.read().strip()

            # XXX: Hardcoded path
            lxc_conf_path = os.path.join(partition_path,
                                         'etc/lxc.conf')
            with open(lxc_conf_path, 'r') as lxc_conf_file:
                requested_status = lxc_conf_file.readline().strip(' \n\r\t#')


            if requested_status == 'started':

                current_status = status(sr_directory, partition_path, name)
                to_start.add(name)

                if requested_status != current_status:
                    start(sr_directory, partition_path, name, lxc_conf_path)


    logger.debug('Container to start %s.', ', '.join(to_start))
    try:
        active_containers = set(call(
            [os.path.join(sr_directory, 'parts/lxc/bin/lxc-ls'),
             '--active']
        ).split('\n'))
        logger.debug('Active containers are %s.', ', '.join(active_containers))
    except SlapContainerError:
        active_containers = set()

    to_stop = active_containers - to_start
    if to_stop:
        logger.debug('Stopping containers %s.', ', '.join(to_stop))

    for container in to_stop:
        try:
            logger.info('Stopping container %s.', container)
            call(
                [os.path.join(sr_directory, 'parts/lxc/bin/lxc-stop'),
                 '-n', container
                ]
            )
        except SlapContainerError:
            logger.fatal('Impossible to stop %s.', container)



def start(sr_directory, partition_path, name, lxc_conf_path):
    lxc_start = os.path.join(sr_directory,
                             'parts/lxc/bin/lxc-start')
    call([lxc_start, '-f', lxc_conf_path,
          '-n', name,
          '-d'])

def status(sr_directory, partition_path, name):
    logger = logging.getLogger('status')
    logger.debug('Check status of %s', name)
    lxc_info = call([os.path.join(sr_directory, 'parts/lxc/bin/lxc-info'),
                     '-n', name])
    if 'RUNNING' in lxc_info:
        return 'started'
    else:
        return 'stopped'



def call(command_line, override_environ={}):
    logger = logging.getLogger('commandline')
    logger.debug('Call %s', ' '.join(command_line))

    environ = dict(os.environ)
    environ.update(override_environ)
    process = subprocess.Popen(command_line, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, env=environ)
    process.stdin.flush()
    process.stdin.close()

    if process.wait() != 0:
        logger.debug('Failed')
        raise SlapContainerError("Subprocess call failed")

    out = process.stdout.read()
    logger.debug('Output : %s.', out)
    return out
