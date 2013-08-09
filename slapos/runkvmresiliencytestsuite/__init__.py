# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Vifib SARL and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

# XXX: takeover module should be in slapos.toolbox, not in slapos.cookbook
from slapos.recipe.addresiliency.takeover import takeover

import slapos.slap

import argparse
import random
import string
import time
import urllib

def parseArguments():
  parser = argparse.ArgumentParser()
  parser.add_argument('--server-url', type=str)
  parser.add_argument('--key-file', type=str)
  parser.add_argument('--cert-file', type=str)
  parser.add_argument('--computer-id', type=str)
  parser.add_argument('--partition-id', type=str)
  parser.add_argument('--software', type=str)
  parser.add_argument('--namebase', type=str)
  parser.add_argument('--kvm-rootinstance-name', type=str)
  args = parser.parse_args()
  return args

def fetchMainInstanceIP(current_partition, software_release, instance_name):
  return current_partition.request(
      software_release=software_release,
      software_type='kvm-resilient',
      partition_reference=instance_name).getConnectionParameter('ipv6')

def setRandomKey(ip):
  """
  Set a random key that will be stored inside of the virtual hard drive.
  """
  random_key = ''.join(random.SystemRandom().sample(string.ascii_lowercase, 20))
  connection = urllib.urlopen('http://%s:10080/set?key=%s' % (ip, random_key))
  if connection.getcode() is not 200:
    raise Exception('Bad return code when setting key in main instance.')
  return random_key

def fetchKey(ip):
  """
  Fetch the key that had been set on original virtual hard drive.
  If doesn't exist (503), fail. If other error: retry after a few minutes,
  fail after XX (2?) hours.
  """
  return urllib.urlopen('http://%s:10080/get' % ip).read().strip()

def main():
  """
  Run KVM Resiliency Test.
  Requires a specific KVM environment (virtual hard drive), see KVM SR for more
  informations.
  """
  # XXX-Cedric: add erp5 scalabilitytest so that we can receive/send informations

  arguments = parseArguments()

  slap = slapos.slap.slap()
  slap.initializeConnection(arguments.server_url, arguments.key_file, arguments.cert_file)
  partition = slap.registerComputerPartition(
      computer_guid=arguments.computer_id,
      partition_id=arguments.partition_id
  )

  ip = fetchMainInstanceIP(partition, arguments.software, arguments.kvm_rootinstance_name)
  print('KVM IP is %s.' % ip)

  key = setRandomKey(ip)
  print('Key set for test in current KVM: %s.' % key)

  # Wait for XX minutes so that replication is done
  sleep_time = 60 * 15#2 * 60 * 60
  print('Sleeping for %s seconds.' % sleep_time)
  time.sleep(sleep_time)

  # Make the clone instance takeover the main instance
  print('Replacing main instance by clone instance...')
  takeover(
      server_url=arguments.server_url,
      key_file=arguments.key_file,
      cert_file=arguments.cert_file,
      computer_guid=arguments.computer_id,
      partition_id=arguments.partition_id,
      software_release=arguments.software,
      namebase=arguments.namebase,
      winner_instance_suffix='1', # XXX: hardcoded value.
  )
  print('Done.')

  # Wait for the new IP (of old-clone new-main instance) to appear.
  print('Waiting for new main instance to be ready...')
  new_ip = None
  while not new_ip or new_ip == 'None' or  new_ip == ip:
    print ip
    print('Not ready yet. New IP is %s' % new_ip)
    time.sleep(60)
    new_ip = fetchMainInstanceIP(partition, arguments.software, arguments.kvm_rootinstance_name)
  print('New IP of instance is %s' % new_ip)

  new_key = None
  for i in range(0, 10):
    try:
      new_key = fetchKey(new_ip)
      break
    except IOError:
      print('Server in new KVM does not answer.')
      time.sleep(60)

  if not new_key:
    raise Exception('Server in new KVM does not answer for too long.')

  print('Key on this new instance is %s' % new_key)

  # Compare with original key. If same: success.
  if new_key == key:
    print('Success')
  else:
    print('Failure')

