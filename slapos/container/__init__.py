# -*- coding: utf-8 -*-

import ConfigParser

import sys
import os

from . import prepare

def main():
    slapos_conf = ConfigParser.ConfigParser()
    slapos_conf.read(sys.argv[1])

    current_binary = os.path.join(os.getcwd(), sys.argv[0])
    binary_directory = os.path.dirname(current_binary)
    sr_directory = os.path.realpath(os.path.join(binary_directory, '..'))

    partition_amount = slapos_conf.getint('slapformat', 'partition_amount')
    partition_base_name = slapos_conf.get('slapformat', 'partition_base_name')
    instance_root = slapos_conf.get('slapos', 'instance_root')
    partition_base_path = os.path.join(instance_root, partition_base_name)
    partition_list = ['%s%d' % (partition_base_path, i)
                      for i in range(partition_amount)]
    bridge_name = slapos_conf.get('slapformat', 'interface_name')

    prepare.main(sr_directory, partition_list, bridge_name)
