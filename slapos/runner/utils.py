import slapos.slap
import time
import subprocess
import os
from xml_marshaller import xml_marshaller
from xml.dom import minidom
import re
import urllib
from flask import jsonify
import shutil
import string
import hashlib
import signal



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

html_escape_table = {
  "&": "&amp;",
  '"': "&quot;",
  "'": "&apos;",
  ">": "&gt;",
  "<": "&lt;",
}
 
def html_escape(text):
  """Produce entities within text."""
  return "".join(html_escape_table.get(c,c) for c in text)


def updateProxy(config):
  if not os.path.exists(config['instance_root']):
    os.mkdir(config['instance_root'])
  slap = slapos.slap.slap()
  #Get current software release profile
  try:
    software_folder = open(os.path.join(config['runner_workdir'],
                                        ".project")).read()
    profile = realpath(config, os.path.join(software_folder,
                                          config['software_profile']))
  except:
    return False

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
  #get instance parameter
  param_path = os.path.join(config['runner_workdir'], ".parameter.xml")
  xml_result = readParameters(param_path)
  if type(xml_result) != type('') and xml_result.has_key('instance'):
    partition_parameter_kw = xml_result['instance']
  else:
    partition_parameter_kw = None
  computer.updateConfiguration(xml_marshaller.dumps(slap_config))
  sr_request = slap.registerOpenOrder().request(profile, partition_reference=partition_reference,
                partition_parameter_kw=partition_parameter_kw, software_type=None,
                filter_kw=None, state=None, shared=False)
  #open(param_path, 'w').write(xml_marshaller.dumps(sr_request.
  #                      getInstanceParameterDict()))
  return True

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
    if not updateProxy(config):
      return False
    slapgrid = Popen([config['slapgrid_sr'], '-vc', config['configuration_file_path']], stdout=logfile)
    writePid(slapgrid_pid, slapgrid.pid)
    slapgrid.wait()
    #Saves the current compile software for re-use
    #This uses the new folder create by slapgrid (if not exits yet)
    data = loadSoftwareData(config['runner_workdir'])
    md5 = ""
    for path in os.listdir(config['software_root']):
      exist = False
      for val in data:
	if val['md5'] == path:
	  exist = True
      conf = os.path.join(config['runner_workdir'], ".project")
      if not exist: #save this compile software folder
	if os.path.exists(conf):
	  data.append({"title":getProjectTitle(config), "md5":path,
	              "path": open(os.path.join(config['runner_workdir'],
	                                        ".project"), 'r').read()})
	  writeSoftwareData(config['runner_workdir'], data)
	else:
	  shutil.rmtree(os.path.join(config['software_root'], path))
	break
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

def killRunningSlapgrid(config, ptype):
  slapgrid_pid = os.path.join(config['runner_workdir'], ptype)
  pid = readPid(slapgrid_pid)
  if pid:
      recursifKill([pid])
  else:
    return False

def recursifKill(pids):
  """Try to kill a list of proccess by the given pid list"""
  if pids == []:
    return
  else:
    for pid in pids:
      ppids = pidppid(pid)
      try:
        os.kill(pid, signal.SIGKILL) #kill current process
      except Exception:
	      pass
      recursifKill(ppids) #kill all children of this process

def pidppid(pid):
  """get the list of the children pids of a process `pid`"""
  proc = Popen('ps -o pid,ppid ax | grep "%d"' % pid, shell=True,
               stdout=subprocess.PIPE)
  ppid  = [x.split() for x in proc.communicate()[0].split("\n") if x]
  return list(int(p) for p, pp in ppid if int(pp) == pid)

def runInstanceWithLock(config):
  slapgrid_pid = os.path.join(config['runner_workdir'], 'slapgrid-cp.pid')
  if not isInstanceRunning(config):
    startProxy(config)
    logfile = open(config['instance_log'], 'w')
    if not updateProxy(config):
      return False
    slapgrid = Popen([config['slapgrid_cp'], '-vc', config['configuration_file_path']], stdout=logfile)
    writePid(slapgrid_pid, slapgrid.pid)
    slapgrid.wait()
    return True
  return False

def getProfilePath(peojectDir, profile):
  if not os.path.exists(os.path.join(peojectDir, ".project")):
    return False
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
      partition_list.append((partition.getId(), partition._connection_dict.copy(),
                              partition._parameter_dict.copy()))
  except Exception:
    pass
  if partition_list:
    for i in xrange(0, int(config['partition_amount'])):
      slappart_id = '%s%s' % ("slappart", i)
      if not [x[0] for x in partition_list if slappart_id==x[0]]:
        partition_list.append((slappart_id, []))
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

def removeInstanceRoot(config):
  if os.path.exists(config['instance_root']):
    svcStopAll(config)
    for root, dirs, files in os.walk(config['instance_root']):
      for fname in dirs:
	fullPath = os.path.join(root, fname)
	if not os.access(fullPath, os.W_OK) :
	  # Some directories may be read-only, preventing to remove files in it
	  os.chmod(fullPath, 0744)
    shutil.rmtree(config['instance_root'])

def getSvcStatus(config):
  result = Popen([config['supervisor'], config['configuration_file_path'],
                  'status']).communicate()[0]
  regex = "(^unix:.+\.socket)|(^error:).*$"
  supervisord = []
  for item in result.split('\n'):
    if item.strip() != "":
      if re.search(regex, item, re.IGNORECASE) == None:
        supervisord.append(re.split('[\s,]+', item))
      else:
        return [] #ignore because it is an error message
  return supervisord

def getSvcTailProcess(config, process):
  return Popen([config['supervisor'], config['configuration_file_path'],
                "tail", process]).communicate()[0]

def svcStartStopProcess(config, process, action):
  cmd = {"RESTART":"restart", "STOPPED":"start", "RUNNING":"stop", "EXITED":"start", "STOP":"stop"}
  return Popen([config['supervisor'], config['configuration_file_path'],
                cmd[action], process]).communicate()[0]

def getFolderContent(config, folder):
  r=['<ul class="jqueryFileTree" style="display: none;">']
  try:
    folder = str(folder)
    r=['<ul class="jqueryFileTree" style="display: none;">']
    d=urllib.unquote(folder)
    realdir = realpath(config, d)
    if not realdir:
      r.append('Could not load directory: Permission denied')
      ldir = []
    else:
      ldir = sorted(os.listdir(realdir), key=str.lower)
    for f in ldir:
      if f.startswith('.'): #do not displays this file/folder
	continue
      ff=os.path.join(d,f)
      if os.path.isdir(os.path.join(realdir,f)):
	r.append('<li class="directory collapsed"><a href="#%s" rel="%s/">%s</a></li>' % (ff, ff,f))
      else:
	e=os.path.splitext(f)[1][1:] # get .ext and remove dot
	r.append('<li class="file ext_%s"><a href="#%s" rel="%s">%s</a></li>' % (e, ff,ff,f))
    r.append('</ul>')
  except Exception,e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))

def getFolder(config, folder):
  r=['<ul class="jqueryFileTree" style="display: none;">']
  try:
    folder = str(folder)
    r=['<ul class="jqueryFileTree" style="display: none;">']
    d=urllib.unquote(folder)
    realdir = realpath(config, d)
    if not realdir:
      r.append('Could not load directory: Permission denied')
      ldir = []
    else:
      ldir = sorted(os.listdir(realdir), key=str.lower)
    for f in ldir:
      if f.startswith('.'): #do not display this file/folder
	continue
      ff=os.path.join(d,f)
      if os.path.isdir(os.path.join(realdir,f)):
	r.append('<li class="directory collapsed"><a href="#%s" rel="%s/">%s</a></li>' % (ff, ff, f))
    r.append('</ul>')
  except Exception,e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))

def getProjectList(folder):
  project = []
  project_list = sorted(os.listdir(folder), key=str.lower)
  for elt in project_list:
    project.append(elt)
  return project

def configNewSR(config, projectpath):
  folder = realpath(config, projectpath)
  if folder:
    if isInstanceRunning(config):
      killRunningSlapgrid(config, "slapgrid-cp.pid")
    if isSoftwareRunning(config):
      killRunningSlapgrid(config, "slapgrid-sr.pid")
    stopProxy(config)
    removeProxyDb(config)
    startProxy(config)
    removeInstanceRoot(config)
    open(os.path.join(config['runner_workdir'], ".project"), 'w').write(projectpath)
    return True
  else:
    return False

def newSoftware(folder, config, session):
  json = ""
  code = 0
  runner_dir = config['runner_workdir']
  try:
    folderPath = realpath(config, folder, check_exist=False)
    if folderPath and not os.path.exists(folderPath):
      os.mkdir(folderPath)
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
      open(os.path.join(folderPath, config['software_profile']), 'w').write(softwareContent)
      open(os.path.join(folderPath, config['instance_profile']), 'w').write(instanceContent)
      open(os.path.join(runner_dir, ".project"), 'w').write(folder + "/")
      session['title'] = getProjectTitle(config)
      code = 1
    else:
      json = "Bad folder or Directory '" + folder + \
        "' already exist, please enter a new name for your software"
  except Exception, e:
    json = "Can not create your software, please try again! : " + str(e)
    if os.path.exists(folderPath):
      shutil.rmtree(folderPath)
  return jsonify(code=code, result=json)

def checkSoftwareFolder(path, config):
  realdir = realpath(config, path)
  if realdir and os.path.exists(os.path.join(realdir, config['software_profile'])):
    return jsonify(result=path)
  return jsonify(result="")

def getProjectTitle(config):
  conf = os.path.join(config['runner_workdir'], ".project")
  if os.path.exists(conf):
    project = open(conf, "r").read().split("/")
    software = project[len(project) - 2]
    return software + " (" + string.join(project[:(len(project) - 2)], '/') + ")"
  return "No Profile"

def loadSoftwareData(runner_dir):
  import pickle
  file_path = os.path.join(runner_dir, '.softdata')
  if not os.path.exists(file_path):
    return []
  pkl_file = open(file_path, 'rb')
  data = pickle.load(pkl_file)
  pkl_file.close()
  return data

def writeSoftwareData(runner_dir, data):
  import pickle
  file_path = os.path.join(runner_dir, '.softdata')
  pkl_file = open(file_path, 'wb')
  # Pickle dictionary using protocol 0.
  pickle.dump(data, pkl_file)
  pkl_file.close()

def removeSoftwareByName(config, folderName):
  if isSoftwareRunning(config) or isInstanceRunning(config):
    return jsonify(code=0, result="Software installation or instantiation in progress, cannot remove")
  path = os.path.join(config['software_root'], folderName)
  if not os.path.exists(path):
    return jsonify(code=0, result="Can not remove software: No such file or directory")
  svcStopAll(config)
  shutil.rmtree(path)
  #update compiled software list
  data = loadSoftwareData(config['runner_workdir'])
  i = 0
  for p in data:
    if p['md5'] == folderName:
      del data[i]
      writeSoftwareData(config['runner_workdir'], data)
      break
    i = i+1
  return jsonify(code=1, result=data)

def tail(f, lines=20):
  """
  Returns the last `lines` lines of file `f`. It is an implementation of tail -f n.
  """
  BUFSIZ = 1024
  f.seek(0, 2)
  bytes = f.tell()
  size = lines + 1
  block = -1
  data = []
  while size > 0 and bytes > 0:
      if bytes - BUFSIZ > 0:
	  # Seek back one whole BUFSIZ
	  f.seek(block * BUFSIZ, 2)
	  # read BUFFER
	  data.insert(0, f.read(BUFSIZ))
      else:
	  # file too small, start from begining
	  f.seek(0,0)
	  # only read what was not read
	  data.insert(0, f.read(bytes))
      linesFound = data[0].count('\n')
      size -= linesFound
      bytes -= BUFSIZ
      block -= 1
  return string.join(''.join(data).splitlines()[-lines:], '\n')

def readFileFrom(f, lastPosition):
  """
  Returns the last lines of file `f`, from position lastPosition.
  and the last position
  """
  BUFSIZ = 1024
  f.seek(0, 2)
  bytes = f.tell()
  block = -1
  data = ""
  length = bytes
  if lastPosition <= 0 and length > 30000:
    lastPosition = length-30000
  size = bytes - lastPosition
  while bytes > lastPosition:
    if abs(block*BUFSIZ) <= size:
      # Seek back one whole BUFSIZ
      f.seek(block * BUFSIZ, 2)
      data = f.read(BUFSIZ) + data
    else:
      margin = abs(block*BUFSIZ) - size
      if length < BUFSIZ:
	f.seek(0,0)
      else:
	seek = block * BUFSIZ + margin
	f.seek(seek, 2)
      data = f.read(BUFSIZ - margin) + data
    bytes -= BUFSIZ
    block -= 1
  f.close()
  return {"content":data, "position":length}

def isText(file):
  """Return True if the mimetype of file is Text"""
  if not os.path.exists(file):
    return False
  text_range = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
  is_binary_string = lambda bytes: bool(bytes.translate(None, text_range))
  try:
    return not is_binary_string(open(file).read(1024))
  except:
    return False

def md5sum(file):
  """Compute md5sum of `file` and return hexdigest value"""
  if os.path.isdir(file):
    return False
  try:
    fh = open(file, 'rb')
    m = hashlib.md5()
    while True:
      data = fh.read(8192)
      if not data:
	break
      m.update(data)
    return m.hexdigest()
  except:
    return False

def realpath(config, path, check_exist=True):
  """Get realpath of path or return False if user is not allowed to access to
  this file"""
  split_path = path.split('/')
  key = split_path[0]
  allow_list = {'software_root':config['software_root'], 'instance_root':
                config['instance_root'], 'workspace': config['workspace']}
  if allow_list.has_key(key):
    del split_path[0]
    path = os.path.join(allow_list[key], string.join(split_path, '/'))
    if check_exist:
      if os.path.exists(path):
	return path
      else:
	return False
    else:
      return path
  return False

def readParameters(path):
  if os.path.exists(path):
    try:
      xmldoc = minidom.parse(path)
      object = {}
      for elt in xmldoc.childNodes:
        sub_object = {}
        for subnode in elt.childNodes:
          if subnode.nodeType != subnode.TEXT_NODE:
            sub_object[str(subnode.getAttribute('id'))] = str(subnode.
	                                                 childNodes[0].data)
	    object[str(elt.tagName)] = sub_object
      return object
    except Exception, e:
      return str(e)
  else:
    return "No such file or directory: " + path