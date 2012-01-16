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
import hashlib
import os
import signal
import shutil
import subprocess

PROCESS = None

class HashFile(object):

  def __init__(self, hash_name):
    if hash_name not in hashlib.algorithms:
      raise ValueError("hash_name is not valid.")
    self._hash = getattr(hashlib, hash_name)()

  def close(self):
    pass

  def digest(self):
    return self._hash.digest()

  def flush(self):
    pass

  def fileno(self):
    raise NotImplementedError("fileno() not implemented on HashFiles")

  def hexdigest(self):
    return self._hash.hexdigest()

  def isatty(self):
    return False

  def next(self):
    raise NotImplementedError("next() not implemented on HashFiles")

  def read(self, size=None):
    raise NotImplementedError("read() not implemented on HashFiles")

  def readlines(self, size=None):
    raise NotImplementedError("readlines() not implemented on HashFiles")

  def tell(self):
    return self._position

  def truncate(self, size=None):
    raise NotImplementedError("truncate([size]) not implemented on HashFiles")

  def write(self, string):
    self._hash.update(string)

  def writelines(self, sequence):
    for line in sequence:
      self.write('%s\n' % line)



class Process(object):

  def __init__(self, command_line, files):
    self.restarting = True

    self.command_line = command_line
    self.files = dict()
    for filename in files:
      if not os.path.exists(filename):
        raise OSError("%s does not exist" % filename)
      self.files[filename] = self.sha512sum(filename)

    self._subprocess = subprocess.Popen(self.command_line)
    self.restarting = False

  def sha512sum(self, filename):
    hash_ = HashFile('sha512')
    with open(filename, 'r') as file_:
      shutil.copyfileobj(file_, hash_)
    return hash_.digest()

  def mainloop(self):
    while self._subprocess.poll() is None:
      signal.pause()
    return self._subprocess.returncode

  def terminate(self):
    if self._subprocess.poll() is None:
      self._subprocess.terminate()

  def restart(self):
    self.restarting = True
    modified = False
    for filename, checksum in self.files.iteritems():
      if not os.path.exists(filename):
        raise OSError("%s does not exist" % filename)
      new_checksum = self.sha512sum(filename)
      if new_checksum != checksum:
        modified = True
      self.files[filename] = new_checksum

    if modified:
      self._subprocess.terminate()
      self._subprocess.wait()
      self._subprocess = subprocess.Popen(self.command_line)
    self.restarting = False


def usr1_handler(signum, frame):
  global PROCESS

  if PROCESS.restarting is False:
    PROCESS.restart()

def main():
  global PROCESS

  parser = argparse.ArgumentParser(
    description="Manager catching SIGUSR1 and reloading application "
                "according if configuration files changed"
  )
  parser.add_argument('-c', '--config', action='append', required=True,
                      help='Configuration file, multiple values')
  parser.add_argument('-p', '--pidfile', action='store', required=False,
                      help='Create a PID file')
  parser.add_argument('argument', nargs='+', help='Command line argument')

  args = parser.parse_args()

  if args.pidfile is not None:
    with open(args.pidfile, 'w') as pid_file:
      pid_file.write('%d' % os.getpid())

  PROCESS = Process(args.argument, args.config)
  signal.signal(signal.SIGUSR1, usr1_handler)
  try:
    return PROCESS.mainloop()
  finally:
    PROCESS.terminate()
    if args.pidfile is not None and os.path.exists(args.pidfile):
      os.unlink(args.pidfile)

if __name__ == '__main__':
  import sys
  sys.exit(main())
