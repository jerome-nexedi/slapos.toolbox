import slapos.slap
import time
import subprocess
import os
from xml_marshaller import xml_marshaller
import re
import urllib
from flask import jsonify
import shutil
import string


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
  profile = getProfilePath(config['runner_workdir'], config['software_profile'])
  slap.initializeConnection(config['master_url'])
  slap.registerSupply().supply(profile, computer_guid=config['computer_id'])
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
  slap.registerOpenOrder().request(profile,
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


def getProfile(peojectDir, profileName):
  profile = getProfilePath(peojectDir, profileName)
  if os.path.exists(profile):
    return open(profile).read()
  else:
    return ''

def getProfilePath(peojectDir, profile):
  if not os.path.exists(os.path.join(peojectDir, ".project")):
    return ""
  projectFolder = open(os.path.join(peojectDir, ".project")).read()
  return os.path.join(projectFolder, profile)

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

def runBuildoutAnnotate(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-sr.pid')
  if not isSoftwareRunning(config):
	bin_buildout = os.path.join(config['software_root'], "bin/buildout")
	if os.path.exists(bin_buildout):
	  logfile = open(config['annotate_log'], 'w')
	  buildout = Popen([bin_buildout, '-vc', config['configuration_file_path'], 
	                    "annotate"], stdout=logfile)
	  buildout.wait()
	  return True
  return False

def svcStopAll(config):
  return Popen([config['supervisor'], config['configuration_file_path'], 
                'shutdown']).communicate()[0]

def getSvcStatus(config):
  result = Popen([config['supervisor'], config['configuration_file_path'], 
                  'status']).communicate()[0]
  regex = "(^unix:.+\.socket)|(^error:).*$"
  supervisord = []
  for item in result.split('\n'):
    if item != "" and re.search(regex, item) == None:
      supervisord.append(re.split('[\s,]+', item))
  return supervisord

def getSvcTailProcess(config, process):
  return Popen([config['supervisor'], config['configuration_file_path'], 
                "tail", process]).communicate()[0]

def svcStartStopProcess(config, process, action):
  cmd = {"RESTART":"restart", "STOPPED":"start", "RUNNING":"stop"}
  return Popen([config['supervisor'], config['configuration_file_path'], 
                cmd[action], process]).communicate()[0]

def getFolderContent(folder):
  r=['<ul class="jqueryFileTree" style="display: none;">']
  try:
    r=['<ul class="jqueryFileTree" style="display: none;">']
    d=urllib.unquote(folder)
    for f in os.listdir(d):
      if f.startswith('.'): #do not displays this file/folder
	continue      
      ff=os.path.join(d,f)
      if os.path.isdir(ff):
	r.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (ff,f))
      else:
	e=os.path.splitext(f)[1][1:] # get .ext and remove dot
	r.append('<li class="file ext_%s"><a href="#" rel="%s">%s</a></li>' % (e,ff,f))
    r.append('</ul>')
  except Exception,e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))

def getFolder(folder):
  r=['<ul class="jqueryFileTree" style="display: none;">']
  try:
    r=['<ul class="jqueryFileTree" style="display: none;">']
    d=urllib.unquote(folder)
    for f in os.listdir(d):
      if f.startswith('.'): #do not display this file/folder
	continue
      ff=os.path.join(d,f)
      if os.path.isdir(ff):
	r.append('<li class="directory collapsed"><a href="#" rel="%s/">%s</a></li>' % (ff, f))
    r.append('</ul>')
  except Exception,e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))

def getProjectList(folder):
  project = []
  for elt in os.listdir(folder):
    project.append(elt)
  return project

def newSoftware(folder, config, session):
  json = ""
  code = 0
  runner_dir = config['runner_workdir']
  try:
    if not os.path.exists(folder):
      os.mkdir(folder)
      #load software.cfg and instance.cfg from http://git.erp5.org
      software = "http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/lamp-template/software.cfg"
      instance = "http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/lamp-template/instance.cfg"
      softwareContent = ""
      instanceContent = ""
      try:
	softwareContent = urllib.urlopen(software).read()
	instanceContent = urllib.urlopen(instance).read()
      except:
	#Software.cfg and instance.cfg content will be empty
	pass
      open(os.path.join(folder, config['software_profile']), 'w').write(softwareContent)
      open(os.path.join(folder, config['instance_profile']), 'w').write(instanceContent)
      open(os.path.join(runner_dir, ".project"), 'w').write(folder)
      session['title'] = getProjectTitle(config)
      code = 1
    else:
      json = "Directory '" + folder + "' already exist, please enter a new name for your software"
  except Exception, e:
    json = "Can not create your software, please try again! : " + str(e)
    if os.path.exists(folder):
      shutil.rmtree(folder)
  return jsonify(code=code, result=json)

def checkSoftwareFolder(path, config):
  tmp = path.split('/')
  del tmp[len(tmp) - 1]
  path = string.join(tmp, '/')
  if os.path.exists(os.path.join(path, config['software_profile'])) and \
     os.path.exists(os.path.join(path, config['instance_profile'])):
    return jsonify(result=path)
  return jsonify(result="")

def getProjectTitle(config):
  conf = os.path.join(config['runner_workdir'], ".project")
  if os.path.exists(conf):
    project = open(conf, "r").read().replace(config['workspace'] + "/", "").split("/")
    software = project[len(project) - 1]
    del project[len(project) - 1]
    return software + "(" + string.join(project, '/') + ")"
  return ""