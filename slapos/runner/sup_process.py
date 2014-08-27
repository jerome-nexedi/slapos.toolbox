import time
import xmlrpclib

from supervisor import childutils

# This mini-library is used to communicate with supervisord process
# It aims to replace the file "process.py"
# For the moment, we keep both for compatibility

def isRunning(config, process):
  server = xmlrpclib.Server(config['supervisord_server'])
  state = server.supervisor.getProcessInfo(process)['state']
  return (True if state == 20 else False)


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
      time.sleep(5)
  return False
