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
import gdbm
from json import loads as unjson
import Queue
import select
from StringIO import StringIO
import socket
import os
import logging
import logging.handlers
import signal
import subprocess
import argparse

cleanup_data = {}

def cleanup(signum=None, frame=None):
  global cleanup_data
  cleanup_functions = dict(
    sockets=lambda sock: sock.close(),
    subprocesses=lambda process: process.terminate(),
    paths=lambda filename: os.unlink(filename),
  )
  for data, function in cleanup_functions.iteritems():
    for item in cleanup_data.get(data, []):
      # Swallow everything !
      try:
        function(item)
      except:
        pass

signal.signal(signal.SIGTERM, cleanup)

class TaskRunner(object):

  def __init__(self):
    self._task = None
    self._command = None
    self._time = None

  def has_running_task(self):
    return self._task is not None and self._task.poll() is None

  def had_previous_task(self):
    return self._task is not None and self._task.poll() is not None

  def get_previous_command(self):
    if not self.has_running_task():
      return self._command
    else:
      return None

  def get_previous_timestamp(self):
    if not self.has_running_task():
      return self._time
    else:
      return None

  def get_previous_returncode(self):
    return self._task.poll()

  def flush(self):
    self._task = None
    self._command = None

  def run(self, command, time):
    global cleanup_data
    self._time = time
    self._command = command
    self._task = subprocess.Popen([command], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  close_fds=True)
    self._task.stdin.flush()
    self._task.stdin.close()
    cleanup_data.update(subprocesses=[self._task])

  def fd(self):
    if not self.has_running_task():
      raise KeyError("No task is running.")
    return self._task.stdout.fileno()

def main():
  global cleanup_data

  parser = argparse.ArgumentParser(
    description="Run a single threaded execution queue.")
  parser.add_argument('--database', nargs=1, required=True,
                      help="Path to the database where the last "
                           "calls are stored")
  parser.add_argument('--loglevel', nargs=1,
                      default='INFO',
                      choices=[i for i in logging._levelNames
                               if isinstance(i, str)],
                      required=False)
  parser.add_argument('-l', '--logfile', nargs=1, required=True,
                      help="Path to the log file.")
  parser.add_argument('-t', '--timeout', nargs=1, required=False,
                      dest='timeout', type=int, default=3)
  parser.add_argument('socket', help="Path to the unix socket")

  args = parser.parse_args()

  socketpath = args.socket
  level = logging._levelNames.get(args.loglevel[0], logging.INFO)

  logger = logging.getLogger("EQueue")
  # Natively support logrotate
  handler = logging.handlers.WatchedFileHandler(args.logfile[0], mode='a')
  logger.setLevel(level)
  formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)
  logger.addHandler(handler)

  unixsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

  unixsocket.bind(socketpath)
  logger.debug("Bind on %r", socketpath)
  unixsocket.listen(2)
  logger.debug("Listen on socket")
  unixsocketfd = unixsocket.fileno()

  db = gdbm.open(args.database[0], 'cs', 0700)

  logger.debug("Open timestamp database")

  cleanup_data.update(sockets=[unixsocket])
  cleanup_data.update(paths=[socketpath])

  logger.info("Starting server on %r", socketpath)

  task_queue = Queue.Queue()
  task_running = TaskRunner()

  try:
    rlist = [unixsocketfd]

    while True:
      rlist_s, wlist_s, xlist_s = select.select(rlist, [], [])

      if unixsocketfd in rlist_s:
        conn, addr = unixsocket.accept()
        logger.debug("Connection with file descriptor %d", conn.fileno())

        conn.settimeout(args.timeout)

        request_string = StringIO()
        segment = None
        try:
          while segment != '':
            segment = conn.recv(1024)
            request_string.write(segment)
        except socket.timeout:
          pass

        command = '127'
        try:
          request = unjson(request_string.getvalue())
          timestamp = request['timestamp']
          command = str(request['command'])
          task_queue.put([command, timestamp])
          logger.info("New command %r at %s", command, timestamp)

        except (ValueError, IndexError) :
          logger.warning("Error during the unserialization of json "
                         "message of %r file descriptor. The message "
                         "was %r", conn.fileno(), request_string.getvalue())

        try:
          conn.send(command)
          conn.close()
        except:
          logger.warning("Couldn't respond to %r", conn.fileno())

      rlist = [unixsocketfd]
      if not task_running.has_running_task():
        if task_running.had_previous_task():
          previous_command = task_running.get_previous_command()
          if task_running.get_previous_returncode() != 0:
            logger.warning("%s finished with non zero status.",
                           previous_command)
          else:
            logger.info("%s finished successfully.", previous_command)
          task_running.flush()
          db[previous_command] = str(task_running.get_previous_timestamp())

        try:
          while True:
            command, timestamp = task_queue.get(False)
            if command not in db or timestamp > int(db[command]):
              logger.info("Running %s", command)
              task_running.run(command, timestamp)
              break
            else:
              logger.info("%s already runned.", command)
        except Queue.Empty:
          logger.info("Task queue is empty. Nothing to do...")

      try:
        rlist.append(task_running.fd())
      except KeyError:
        pass

  finally:
    cleanup()

if __name__ == '__main__':
  main()
