# pylint: disable-msg=W0311,C0103

import os
import signal
import time
import xmlrpclib

# This mini-library is used to communicate with supervisord process
# It aims to replace the file "process.py"
# For the moment, we keep both for compatibility


def isRunning(config, process):
  """
  Ask supervisor if given process is currently running
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  state = server.supervisor.getProcessInfo(process)['state']
  return (True if state in (10, 20) else False)


def killRunningProcess(config, process, sig=signal.SIGTERM):
  """
  Send signal "sig" to given process.
  Default signal sent is SIGTERM
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  pid = server.supervisor.getProcessInfo(process)['pid']
  if pid != 0:
    os.kill(pid, sig)


def returnCode(config, process):
  """
  Get the returned code of the last run of given process
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  code = server.supervisor.getProcessInfo(process)['exitstatus']
  return code


def runProcess(config, process):
  """
  Start a process registered by supervisor
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  server.supervisor.startProcess(process)


def runProcesses(config, processes):
  """
  Start by supervisor a list of given processes, one by one
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  for proc in processes:
    server.supervisor.startProcess(proc)
    waitForProcessEnd(config, proc)


def stopProcess(config, process):
  """
  Ask supervisor to stop a process
  """
  if isRunning(config, process):
    server = xmlrpclib.Server(config['supervisord_server'])
    server.supervisor.stopProcess(process)


def stopProcesses(config, processes):
  """
  Stop a list of processes
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  for proc in processes:
    server.supervisor.stopProcess(proc)


def waitForProcessEnd(config, process):
  """
  Block program's execution until given process quits Running state
  """
  server = xmlrpclib.Server(config['supervisord_server'])
  while True:
    state = server.supervisor.getProcessInfo(process)['state']
    if state == 20:
      time.sleep(3)
    else:
      return True
  return False
