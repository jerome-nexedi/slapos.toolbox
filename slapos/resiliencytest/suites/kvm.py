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

import logging
import argparse
import random
import string
import time
import urllib

logger = logging.getLogger('KVMResiliencyTest')

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
  for i in range(0, 60):
    connection = urllib.urlopen('http://%s:10080/set?key=%s' % (ip, random_key))
    if connection.getcode() is 200:
      break
    else:
      logger.info('Impossible to connect to virtual machine to set key. sleeping...')
      time.sleep(60)

    if i is 59:
      raise Exception('Bad return code when setting key in main instance, after trying for 60 minutes.')
  
  return random_key


def fetchKey(ip):
  """
  Fetch the key that had been set on original virtual hard drive.
  If doesn't exist (503), fail. If other error: retry after a few minutes,
  fail after XX (2?) hours.
  """
  new_key = None
  for i in range(0, 10):
    try:
      new_key = urllib.urlopen('http://%s:10080/get' % ip).read().strip()
      break
    except IOError:
      logger.error('Server in new KVM does not answer.')
      time.sleep(60)

  if not new_key:
    raise Exception('Server in new KVM does not answer for too long.')

  return new_key

def runTestSuite(server_url, key_file, cert_file,
                 computer_id, partition_id, software,
                 namebase, kvm_rootinstance_name):
  """
  Run KVM Resiliency Test.
  Requires a specific KVM environment (virtual hard drive), see KVM SR for more
  informations.
  """
  slap = slapos.slap.slap()
  slap.initializeConnection(server_url, key_file, cert_file)
  partition = slap.registerComputerPartition(
      computer_guid=computer_id,
      partition_id=partition_id
  )

  ip = fetchMainInstanceIP(partition, software, kvm_rootinstance_name)
  logger.info('KVM IP is %s.' % ip)

  key = setRandomKey(ip)
  logger.info('Key set for test in current KVM: %s.' % key)

  # Wait for XX minutes so that replication is done
  sleep_time = 60 * 15#2 * 60 * 60
  logger.info('Sleeping for %s seconds.' % sleep_time)
  time.sleep(sleep_time)

  # Make the clone instance takeover the main instance
  logger.info('Replacing main instance by clone instance...')
  takeover(
      server_url=server_url,
      key_file=key_file,
      cert_file=cert_file,
      computer_guid=computer_id,
      partition_id=partition_id,
      software_release=software,
      namebase=namebase,
      winner_instance_suffix='1', # XXX: hardcoded value.
  )
  logger.info('Done.')

  # Wait for the new IP (of old-clone new-main instance) to appear.
  logger.info('Waiting for new main instance to be ready...')
  new_ip = None
  while not new_ip or new_ip == 'None' or  new_ip == ip:
    logger.info('Not ready yet. SlapOS says main IP is %s' % new_ip)
    time.sleep(60)
    new_ip = fetchMainInstanceIP(partition, software, kvm_rootinstance_name)
  logger.info('New IP of instance is %s' % new_ip)

  new_key = fetchKey(new_ip)
  logger.info('Key on this new instance is %s' % new_key)

  # Compare with original key. If same: success.
  # XXX TODO
  if new_key == key:
    logger.info('Success')
    return True
  else:
    logger.error('Failure')
    return False

# Used if launched as standalone script
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

def main():
  arguments = parseArguments()
  runTestCase(arguments.server_url, arguments.key_file, arguments.cert_file,
              arguments.computer_id, arguments.partition_id, arguments.software,
              arguments.namebase, arguments.kvm_rootinstance_name)

if __name__ == '__main__':
  main()

