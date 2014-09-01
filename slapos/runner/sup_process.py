import os
import signal
import time
import xmlrpclib

# This mini-library is used to communicate with supervisord process
# It aims to replace the file "process.py"
# For the moment, we keep both for compatibility


def isRunning(config, process):
  server = xmlrpclib.Server(config['supervisord_server'])
  state = server.supervisor.getProcessInfo(process)['state']
  return (True if state in (10, 20) else False)


def killRunningProcess(config, process, sig=signal.SIGTERM):
  server = xmlrpclib.Server(config['supervisord_server'])
  pid = server.supervisor.getProcessInfo(process)['pid']
  if pid != 0:
    os.kill(pid, sig)


def returnCode(config, process):
  server = xmlrpclib.Server(config['supervisord_server'])
  code = server.supervisor.getProcessInfo(process)['exitstatus']
  return code


def runProcess(config, process):
  server = xmlrpclib.Server(config['supervisord_server'])
  server.supervisor.startProcess(process)


def runProcesses(config, processes):
  server = xmlrpclib.Server(config['supervisord_server'])
  for proc in processes:
    server.supervisor.startProcess(proc)
    waitForProcessEnd(proc)


def stopProcess(config, process):
  """
  Ask supervisor to stop a process
  """
  if isRunning(config, process):
    server = xmlrpclib.Server(config['supervisord_server'])
    server.supervisor.stopProcess(process)


def stopProcesses(config, processes):
  server = xmlrpclib.Server(config['supervisord_server'])
  for proc in processes:
    server.supervisor.stopProcess(proc)


def waitForProcessEnd(config, process):
  server = xmlrpclib.Server(config['supervisord_server'])
  while True:
    state = server.supervisor.getProcessInfo(process)['state']
    if state == 20:
      time.sleep(3)
    else:
      return True
  return False
