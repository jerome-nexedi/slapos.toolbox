import slapos.slap
import time
import subprocess
import os
from xml_marshaller import xml_marshaller


class Popen(subprocess.Popen):
  def __init__(self, *args, **kwargs):
    kwargs['stdin'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.STDOUT
    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('close_fds', True)
    subprocess.Popen.__init__(self, *args, **kwargs)
    self.stdin.flush()
    self.stdin.close()
    self.stdin = None


def updateProxy(config):
  if not os.path.exists(config['instance_root']):
    os.mkdir(config['instance_root'])
  slap = slapos.slap.slap()
  slap.initializeConnection(config['master_url'])
  slap.registerSupply().supply(config['software_profile'], computer_guid=config['computer_id'])
  computer = slap.registerComputer(config['computer_id'])
  prefix = 'slappart'
  slap_config = {
 'address': config['ipv4_address'],
 'instance_root': config['instance_root'],
 'netmask': '255.255.255.255',
 'partition_list': [
                    ],
 'reference': config['computer_id'],
 'software_root': config['software_root']}
  for i in xrange(0, int(config['partition_amount'])):
    partition_reference = '%s%s' % (prefix, i)
    partition_path = os.path.join(config['instance_root'], partition_reference)
    if not os.path.exists(partition_path):
      os.mkdir(partition_path)
    os.chmod(partition_path, 0750)
    slap_config['partition_list'].append({'address_list': [{'addr': config['ipv4_address'],
                                       'netmask': '255.255.255.255'},
                                      {'addr': config['ipv6_address'],
                                       'netmask': 'ffff:ffff:ffff::'},
                      ],
                     'path': partition_path,
                     'reference': partition_reference,
                     'tap': {'name': partition_reference},
                     })

  computer.updateConfiguration(xml_marshaller.dumps(slap_config))
  slap.registerOpenOrder().request(config['software_profile'],
              partition_reference=partition_reference)


def readPid(file):
  if os.path.exists(file):
    data = open(file).read().strip()
    try:
      return int(data)
    except Exception:
      return 0
  return 0


def writePid(file, pid):
  open(file, 'w').write(str(pid))


def startProxy(config):
  proxy_pid = os.path.join(config['runner_workdir'], 'proxy.pid')
  pid = readPid(proxy_pid)
  running = False
  if pid:
    try:
      os.kill(pid, 0)
    except Exception:
      pass
    else:
      running = True
  if not running:
    proxy = Popen([config['slapproxy'], config['configuration_file_path']])
    proxy_pid = os.path.join(config['runner_workdir'], 'proxy.pid')
    writePid(proxy_pid, proxy.pid)
    time.sleep(5)


def stopProxy(config):
  pid = readPid(os.path.join(config['runner_workdir'], 'proxy.pid'))
  if pid:
    try:
      os.kill(pid)
    except:
      pass


def removeProxyDb(config):
  if os.path.exists(config['database_uri']):
    os.unlink(config['database_uri'])

def isSoftwareRunning(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-sr.pid')
  pid = readPid(slapgrid_pid)
  if pid:
    try:
      os.kill(pid, 0)
    except Exception:
      running = False
    else:
      running = True
  else:
    running = False
  return running


def runSoftwareWithLock(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-sr.pid')
  if not isSoftwareRunning(config):
    if not os.path.exists(config['software_root']):
      os.mkdir(config['software_root'])
    stopProxy(config)
    removeProxyDb(config)
    startProxy(config)
    logfile = open(config['software_log'], 'w')
    updateProxy(config)
    slapgrid = Popen([config['slapgrid_sr'], '-vc', config['configuration_file_path']], stdout=logfile)
    writePid(slapgrid_pid, slapgrid.pid)
    slapgrid.wait()
    return True
  return False


def isInstanceRunning(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-cp.pid')
  pid = readPid(slapgrid_pid)
  if pid:
    try:
      os.kill(pid, 0)
    except Exception:
      running = False
    else:
      running = True
  else:
    running = False
  return running


def runInstanceWithLock(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-cp.pid')
  if not isInstanceRunning(config):
    startProxy(config)
    logfile = open(config['instance_log'], 'w')
    updateProxy(config)
    slapgrid = Popen([config['slapgrid_cp'], '-vc', config['configuration_file_path']], stdout=logfile)
    writePid(slapgrid_pid, slapgrid.pid)
    slapgrid.wait()
    return True
  return False


def getProfile(profile):
  if os.path.exists(profile):
    return open(profile).read()
  else:
    return ''


def getSlapStatus(config):
  slap = slapos.slap.slap()
  slap.initializeConnection(config['master_url'])
  partition_list = []
  computer = slap.registerComputer(config['computer_id'])
  try:
    for partition in computer.getComputerPartitionList():
      # Note: Internal use of API, as there is no reflexion interface in SLAP
      partition_list.append((partition.getId(), partition._connection_dict.copy()))
  except Exception:
    pass
  return partition_list


def svcStopAll(config):
  return Popen([config['supervisor'], config['configuration_file_path'], 'shutdown']).communicate()[0]

def getSvcStatus(config):
  return Popen([config['supervisor'], config['configuration_file_path'], 'status']).communicate()[0]
