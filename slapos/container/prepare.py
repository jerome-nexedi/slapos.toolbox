# -*- coding: utf-8 -*-

import ConfigParser
import os

import lockfile

def main(sr_directory, partition_list):

    overall_failure = 0
    for partition_path in partition_list:
        slapcontainer_filename = os.path.join(partition_path,
                                              '.slapcontainer')
        if os.path.isfile(slapcontainer_filename):
            failure = 0
            lock = lockfile.FileLock(slapcontainer_filename)
            try:
                lock.acquire(timeout=0)
                slapcontainer_conf = ConfigParser.ConfigParser()
                slapcontainer_conf.read(slapcontainer_filename)

                requested_status = slapcontainer_conf.get('requested', 'status')

                if not slapcontainer_conf.has_section('current'):
                    slapcontainer_conf.add_section('current')
                if not slapcontainer_conf.has_option('current', 'created'):
                    slapcontainer_conf.set('current', 'created', 'no')
                if not slapcontainer_conf.has_option('current', 'status'):
                    slapcontainer_conf.set('current', 'status', 'stopped')

                if requested_status == 'started':
                    failure |= start(sr_directory, partition_path,
                                     slapcontainer_conf)
                else:
                    failure |= stop(sr_directory, partition_path,
                                    slapcontainer_conf)

                with open(slapcontainer_filename, 'w') as slapcontainer_fp:
                    slapcontainer_conf.write(slapcontainer_fp)
            except lockfile.LockTimeout:
                # Can't do anything, we'll see on the next run
                pass
            finally:
                lock.release()

            overall_failure |= failure

        return overall_failure



def start(sr_directory, partition_path, conf):
    failure = 0
    if conf.get('current', 'created') == 'no':
        failure |= create(sr_directory, partition_path, conf)

    if failure:
        return failure
    else:
        conf.set('current', 'created', 'yes')

    # TODO: Check if container is started,
    #       Start container

    conf.set('current', 'status', 'started')

    return failure



def stop(sr_directory, partition_path, conf):
    failure = 0

    # TODO : Check if container is stopped
    #        Stop container

    if conf.get('current', 'created') == 'yes':
        failure |= destroy(partition_path, conf)

    return failure



def create(sr_directory, partition_path, conf):
    failure = 0

    # TODO : Create container

    return failure



def destroy(partition_path, conf):
    failure = 0

    # TODO: Destroy container

    return failure
