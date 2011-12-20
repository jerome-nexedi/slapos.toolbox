##############################################################################
#
# Copyright (c) 2010 Vifib SARL and Contributors. All Rights Reserved.
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
from cStringIO import StringIO
import inotifyx
import json
import math
import os
import re
import socket
import subprocess
import time

def wait_for_creation(filepath):
  creation_fd = inotifyx.init()
  try:
    parent_directory, filename = os.path.split(filepath)
    inotifyx.add_watch(creation_fd, parent_directory, inotifyx.IN_CREATE)
    if os.path.exists(filepath):
      if not os.path.isfile(filepath):
        raise ValueError("%s isn't a file." % filepath)
    else:
      while True:
        events = inotifyx.get_events(creation_fd)
        if filename in [e.name for e in events]:
          break
  finally:
    os.close(creation_fd)

def follow_each_line(filepath, rotated):
  mask = inotifyx.IN_MODIFY
  if rotated:
    mask |= inotifyx.IN_MOVE_SELF | inotifyx.IN_DELETE_SELF

  follow_fd = inotifyx.init()
  position = 0
  queued_data = StringIO()
  try:
    inotifyx.add_watch(follow_fd, filepath, mask)
    while True:
      events = inotifyx.get_events(follow_fd)
      for e in events:
        # File has been moved
        if e.mask & inotifyx.IN_MOVE_SELF or e.mask & inotifyx.IN_DELETE_SELF:
          # Watch the new file when created.
          position = 0
          wait_for_creation(filepath)
          os.close(follow_fd)
          follow_fd = inotifyx.init()
          inotifyx.add_watch(follow_fd, filepath, mask)
          break
        # The file has been modified
        else:
          with open(filepath) as log_file:
            log_file.seek(position)
            queued_data.write(log_file.read())
            position = log_file.tell()
          temp = queued_data.getvalue().split('\n')
          # Remove the last item which could be a partially written line and
          # buffer it.
          queued_data = StringIO()
          queued_data.write(temp.pop(-1))
          for line in temp:
            yield line
  finally:
    os.close(follow_fd)

def run():

  parser = argparse.ArgumentParser(description="Log follower.")
  parser.add_argument('--callback', '-c', help="Executable to call once the "
                                               "regular expression is detected.",
                      required=True)
  parser.add_argument('--equeue-socket', '-e', default=None, metavar='SOCKET',
                      help="Specify a equeue socket. If there's no equeue "
                           "logfollower will run the command itself.")
  parser.add_argument('-n', help="Number of occurrences of regular expression "
                                 "to trigger the callback.", default=1,
                      type=int)
  parser.add_argument('--regex', '-r', help="Regular expression which "
                                            "trigger the callback.",
                      required=True)
  parser.add_argument('--rotated', action='store_const', default=False,
                      const=True, help="Specify that the logfile can be "
                                       "rotated. This will detect the "
                                       "rotation and reload it.")
  parser.add_argument('--wait-for-creation', action='store_const', default=False,
                      const=True, help="Wait for the log file creation.")
  parser.add_argument('logfile', metavar='LOGFILE', nargs=1,
                      help="Log file to follow.")
  args = parser.parse_args()

  if not os.path.exists(args.callback):
    parser.error("Callback should exist.")

  try:
    regex = re.compile(args.regex)
  except:
    parser.error("Bad regular expression.")

  log_filename = os.path.abspath(os.path.join(os.getcwd(), args.logfile[0]))

  if args.wait_for_creation:
    try:
      wait_for_creation(log_filename)
    except:
      return 1 # Exit failure
  elif not os.path.isfile(log_filename):
    return 1 # Exit failure

  occurrences = 0
  for line in follow_each_line(log_filename, args.rotated):
    if regex.match(line.strip()):
      occurrences += 1
    if occurrences >= args.n:
      occurrences = 0
      print "Run callback."
      if args.equeue_socket is not None:
        equeue_request = json.dumps(dict(
          command=args.callback,
          timestamp=int(math.ceil(time.time())),
        ))
        equeue_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        equeue_socket.connect(args.equeue_socket)
        equeue_socket.send(equeue_request)
        result = equeue_socket.recv(len(args.callback))
        equeue_socket.close()

        if result != args.callback:
          raise SystemExit(1)
      else:
        callback = subprocess.Popen([args.callback], stdin=subprocess.PIPE)
        callback.stdin.flush()
        callback.stdin.close()
        if callback.wait() != 0:
          print "Callback return a non-zero status."
        else:
          print "Callback ran successfully."

if __name__ == '__main__':
  import sys
  sys.exit(run())
