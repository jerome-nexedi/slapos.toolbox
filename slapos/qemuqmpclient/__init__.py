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

import argparse
import json
import os
import socket
import time

QMP_STOP_ACTION = 'suspend'
QMP_RESUME_ACTION = 'resume'
QMP_CAPABILITIES_ACTION = 'capabilities'

def parseArgument():
  """
  Very basic argument parser. Might blow up for anything else than
  "./executable mysocket.sock stop/resume".
  """
  parser = argparse.ArgumentParser()
  parser.add_argument('unix_socket_location')
  parser.add_argument(
      'action',
      choices=[QMP_STOP_ACTION, QMP_RESUME_ACTION, QMP_CAPABILITIES_ACTION]
  )
  args = parser.parse_args()
  return args.unix_socket_location, args.action


class QemuQMPWrapper(object):
  """
  Small wrapper around Qemu's QMP to control a qemu VM.
  See http://git.qemu.org/?p=qemu.git;a=blob;f=qmp-commands.hx for
  QMP API definition.
  """
  def __init__(self, unix_socket_location):
    self.socket = self.connectToQemu(unix_socket_location)
    self.capabilities()

  @staticmethod
  def connectToQemu(unix_socket_location):
    """
    Create a socket, connect to qemu, be sure it answers, return socket.
    """
    if not os.path.exists(unix_socket_location):
      raise Exception('unix socket %s does not exist.' % unix_socket_location)

    print 'Connecting to qemu...'
    so = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connected = False
    while not connected:
      try:
        so.connect(unix_socket_location)
      except socket.error:
        time.sleep(1)
        print 'Could not connect, retrying...'
      else:
        connected = True
    so.recv(1024)

    return so


  def _send(self, message):
    self.socket.send(json.dumps(message))
    data = self.socket.recv(1024)
    try:
      return json.loads(data)
    except ValueError:
      print 'Wrong data: %s' % data

  def _getVMStatus(self):
    response = self._send({'execute': 'query-status'})
    if response:
      return self._send({'execute': 'query-status'})['return']['status']
    else:
      raise IOError('Empty answer')

  def _waitForVMStatus(self, wanted_status):
    while True:
      try:
        actual_status = self._getVMStatus()
        if actual_status == wanted_status:
          return
        else:
          print 'VM in %s status, wanting it to be %s, retrying...' % (
              actual_status, wanted_status)
          time.sleep(1)
      except IOError:
          print 'VM not ready, retrying...'


  def capabilities(self):
    print 'Asking for capabilities...'
    self._send({'execute': 'qmp_capabilities'})

  def suspend(self):
    print 'Suspending VM...'
    self._send({'execute': 'stop'})
    self._waitForVMStatus('paused')

  def resume(self):
    print 'Resuming VM...'
    self._send({'execute': 'cont'})
    self._waitForVMStatus('running')


def main():
  unix_socket_location, action = parseArgument()
  qemu_wrapper = QemuQMPWrapper(unix_socket_location)

  if action == QMP_STOP_ACTION:
    qemu_wrapper.suspend()
  elif action == QMP_RESUME_ACTION:
    qemu_wrapper.resume()
  elif action == QMP_CAPABILITIES_ACTION:
    qemu_wrapper.capabilities()

if __name__ == '__main__':
  main()
