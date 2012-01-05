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
import os
import sys
import signal
import struct

children = []
execution_failed = False

def run_executable(executable, redirect_stderr):
  if redirect_stderr:
    # Redirect stderr to stdout
    # and      stderr to devnull
    stderr_fileno = sys.stderr.fileno()
    stdout_fileno = sys.stdout.fileno()
    null_fileno = os.open(os.devnull, os.O_WRONLY)

    os.close(stderr_fileno)
    os.dup2(stdout_fileno, stderr_fileno)
    os.dup2(null_fileno, stdout_fileno)
    os.close(null_fileno)
  os.execl(executable, executable)

def forkandrun(executable, redirect_stderr):
  global children
  try:
    pid = os.fork()
    if pid > 0: # Parent process
      children.append(pid)
    else: # Children process
      run_executable(executable, redirect_stderr)
  except OSError:
    print >> sys.stderr, "Failed to run %r" % executable

def split_status(status_code):
  return struct.unpack('BB', struct.pack('H', status_code))

def main():
  global children, execution_failed

  def sigchld_handler(signum, frame):
    global children, execution_failed
    pid, status = os.wait()
    exitcode, sigcode = split_status(status)
    if exitcode != 0 or sigcode != 0:
      execution_failed = True
    children.remove(pid)

  def sigterm_handler(signum, frame):
    global children
    for pid in children:
      try:
        os.kill(pid, signal.SIGTERM)
      except:
        pass
    raise SystemExit

  signal.signal(signal.SIGTERM, sigterm_handler)
  signal.signal(signal.SIGCHLD, sigchld_handler)

  argument_parser = argparse.ArgumentParser(
    description="Execute binary list of executable after the first one has "
                "finished. This uses fork and wait for child. Sending a "
                "SIGTERM to this program will properly send a SIGTERM to its "
                "children."
  )
  argument_parser.add_argument('--stdout', required=False, action='store_true',
                               help="Redirect stderr on stdout and ignore "
                                    "stdout.")
  argument_parser.add_argument('--first-one', '-f', metavar='main',
                               required=True,
                               help='First executable to run.')
  argument_parser.add_argument('executables', metavar='executable', nargs='+')
  arguments = argument_parser.parse_args()

  forkandrun(arguments.first_one, arguments.stdout)
  while children:
    signal.pause()
  if not execution_failed:
    for executable in arguments.executables:
      forkandrun(executable, arguments.stdout)
    while children:
      signal.pause()
  else:
    if arguments.stdout:
      output = sys.stdout
    else:
      output = sys.stderr
    print >> output, "Failed to run the first executable."

  if execution_failed:
    return 1
  return 0


if __name__ == '__main__':
  sys.exit(main())
