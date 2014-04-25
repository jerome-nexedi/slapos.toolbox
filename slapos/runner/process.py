import os
import psutil
import signal
import subprocess
import sys

SLAPRUNNER_PROCESS_LIST = []


class Popen(subprocess.Popen):
  """
  Extension of Popen to launch and kill processes in a clean way
  """
  def __init__(self, *args, **kwargs):
    """
    Launch process and add object to process list for handler
    """
    self.name = kwargs.pop('name', None)
    kwargs['stdin'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('close_fds', True)
    subprocess.Popen.__init__(self, *args, **kwargs)
    SLAPRUNNER_PROCESS_LIST.append(self)
    self.stdin.flush()
    self.stdin.close()
    self.stdin = None

  def kill(self, sig=signal.SIGTERM, recursive=False):
    """
    Kill process and all its descendants if recursive
    """
    if self.poll() is None:
      if recursive:
        childs_pids = pidppid(self.pid)
        for pid in childs_pids:
          killNoFail(pid, sig)
      killNoFail(self.pid, sig)
      if self.poll() is not None:
        SLAPRUNNER_PROCESS_LIST.remove(self)

  def __del__(self):
    """
    Del function, try to kill process group
    and process if its group does not exist
    """
    for pid in (-self.pid, self.pid):
      try:
        os.kill(-self.pid, 15)
      except OSError:
        pass
    subprocess.Popen.__del__(self)


def pidppid(pid, recursive=True):
  """
  Return a list of all children of pid
  """
  return [p.pid for p in psutil.Process(pid).get_children(recursive=recursive)]


def killNoFail(pid, sig):
  """
  function to kill without failing. Return True if kill do not fail
  """
  try:
    os.kill(pid, sig)
    return True
  except OSError:
    return False


def isRunning(name):
  """
  Return True if a process with this name is running
  """
  for process in SLAPRUNNER_PROCESS_LIST:
    if process.name == name:
      if process.poll() is None:
        return True
  return False


def killRunningProcess(name, recursive=False):
  """
  Kill all processes with a given name
  """
  for process in SLAPRUNNER_PROCESS_LIST:
    if process.name == name:
      process.kill(recursive=recursive)


def handler(sig, frame):
  """
  Signal handler to kill all processes
  """
  pid = os.getpid()
  os.kill(-pid, sig)
  sys.exit()


def setHandler(sig_list=None):
  if sig_list is None:
    sig_list = [signal.SIGTERM]
  for sig in sig_list:
    signal.signal(sig, handler)


def isPidFileProcessRunning(pidfile):
  """
  Test if the pidfile exist and if the process is still active
  """
  if os.path.exists(pidfile):
    try:
      pid = int(open(pidfile, 'r').readline())
    except ValueError:
      pid = None
    # XXX This could use psutil library.
    if pid and os.path.exists("/proc/%s" % pid):
      return True
    return False
