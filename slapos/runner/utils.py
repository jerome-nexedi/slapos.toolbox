# -*- coding: utf-8 -*-
# vim: set et sts=2:
# pylint: disable-msg=W0311,C0301,C0103,C0111,W0141,W0142


import logging
import md5
import multiprocessing
import re
import shutil
import os
import time
import urllib
from xml.dom import minidom

import xml_marshaller
from flask import jsonify

from slapos.runner.process import Popen, isRunning, killRunningProcess
from slapos.htpasswd import HtpasswdFile
import slapos.slap

# Setup default flask (werkzeug) parser

logger = logging.getLogger('werkzeug')


html_escape_table = {
  "&": "&amp;",
  '"': "&quot;",
  "'": "&apos;",
  ">": "&gt;",
  "<": "&lt;",
}


def html_escape(text):
  """Produce entities within text."""
  return "".join(html_escape_table.get(c, c) for c in text)


def getSession(config):
  """
  Get the session data of current user.
  Returns:
    a list of user information or None if the file does not exist.
  """
  user_path = os.path.join(config['etc_dir'], '.users')
  if os.path.exists(user_path):
    return open(user_path).read().split(';')


def saveSession(config, account):
  """
  Save account information for the current user

  Args:
    config: Slaprunner configuration
    session: Flask session
    account: New session data to be save

  Returns:
    True if all goes well or str (error message) if fail
  """
  # XXX Cedric LN hardcoded path for files
  user = os.path.join(config['etc_dir'], '.users')
  htpasswdfile = os.path.join(config['etc_dir'], '.htpasswd')
  backup = False
  try:
    if os.path.exists(user):
      #backup previous data
      data = open(user).read()
      open('%s.back' % user, 'w').write(data)
      backup = True
      if not account[1]:
        account[1] = data.split(';')[1]
    #save new account data
    open(user, 'w').write((';'.join(account)).encode("utf-8"))
    # Htpasswd file for cloud9
    # XXX Cedric Le N order of account list values suppose to be fixed
    # Remove former file to avoid aoutdated accounts
    if os.path.exists(htpasswdfile):
      os.remove(htpasswdfile)
    passwd = HtpasswdFile(htpasswdfile, create=True)
    passwd.update(account[0], account[1])
    passwd.save()
    return True
  except Exception as e:
    try:
      if backup:
        os.remove(user)
        os.rename('%s.back' % user, user)
    except:
      pass
    return str(e)


def getCurrentSoftwareReleaseProfile(config):
  """
  Returns used Software Release profile as a string.
  """
  try:
    software_folder = open(
        os.path.join(config['etc_dir'], ".project")).read()
    return realpath(
        config, os.path.join(software_folder, config['software_profile']))
  except:
    return False


def requestInstance(config, software_type=None):
  """
  Request the main instance of our environment
  """
  software_type_path = os.path.join(config['etc_dir'], ".software_type.xml")
  if software_type:
    # Write it to conf file for later use
    open(software_type_path, 'w').write(software_type)
  elif os.path.exists(software_type_path):
    software_type = open(software_type_path).read()
  else:
    software_type = 'default'

  slap = slapos.slap.slap()
  profile = getCurrentSoftwareReleaseProfile(config)
  slap.initializeConnection(config['master_url'])

  param_path = os.path.join(config['etc_dir'], ".parameter.xml")
  xml_result = readParameters(param_path)
  partition_parameter_kw = None
  if type(xml_result) != type('') and 'instance' in xml_result:
    partition_parameter_kw = xml_result['instance']

  return slap.registerOpenOrder().request(
      profile,
      partition_reference=getSoftwareReleaseName(config),
      partition_parameter_kw=partition_parameter_kw,
      software_type=software_type,
      filter_kw=None,
      state=None,
      shared=False)


def updateProxy(config):
  """
  Configure Slapos Node computer and partitions.
  Send current Software Release to Slapproxy for compilation and deployment.
  """
  if not os.path.exists(config['instance_root']):
    os.mkdir(config['instance_root'])
  slap = slapos.slap.slap()
  profile = getCurrentSoftwareReleaseProfile(config)

  slap.initializeConnection(config['master_url'])
  slap.registerSupply().supply(profile, computer_guid=config['computer_id'])
  computer = slap.registerComputer(config['computer_id'])
  prefix = 'slappart'
  slap_config = {
    'address': config['ipv4_address'],
    'instance_root': config['instance_root'],
    'netmask': '255.255.255.255',
    'partition_list': [],
    'reference': config['computer_id'],
    'software_root': config['software_root']
  }

  for i in xrange(0, int(config['partition_amount'])):
    partition_reference = '%s%s' % (prefix, i)
    partition_path = os.path.join(config['instance_root'], partition_reference)
    if not os.path.exists(partition_path):
      os.mkdir(partition_path)
    os.chmod(partition_path, 0750)
    slap_config['partition_list'].append({
                                           'address_list': [
                                              {
                                                'addr': config['ipv4_address'],
                                                'netmask': '255.255.255.255'
                                              }, {
                                                'addr': config['ipv6_address'],
                                                'netmask': 'ffff:ffff:ffff::'
                                              },
                                           ],
                                           'path': partition_path,
                                           'reference': partition_reference,
                                           'tap': {'name': partition_reference}})
  computer.updateConfiguration(xml_marshaller.xml_marshaller.dumps(slap_config))
  return True


def updateInstanceParameter(config, software_type=None):
  """
  Reconfigure Slapproxy to re-deploy current Software Instance with parameters.

  Args:
    config: Slaprunner configuration.
    software_type: reconfigure Software Instance with software type.
  """
  if not (updateProxy(config) and requestInstance(config, software_type)):
    return False


def startProxy(config):
  """Start Slapproxy server"""
  if isRunning('slapproxy'):
    return

  log = os.path.join(config['log_dir'], 'slapproxy.log')
  Popen([config['slapproxy'], '--log_file', log,
         config['configuration_file_path']],
        name='slapproxy',
        stdout=None)
  time.sleep(4)


def stopProxy(config):
  """Stop Slapproxy server"""
  pass


def removeProxyDb(config):
  """Remove Slapproxy database, this is use to initialize proxy for example when
    configuring new Software Release"""
  if os.path.exists(config['database_uri']):
    os.unlink(config['database_uri'])


def isSoftwareRunning(config=None):
  """
    Return True if slapgrid-sr is still running and false if slapgrid if not
  """
  # XXX-Marco what is 'config' for?
  return isRunning('slapgrid-sr')


def runSoftwareWithLock(config):
  """
    Use Slapgrid to compile current Software Release and wait until
    compilation is done
  """
  if isSoftwareRunning():
    return False

  slapgrid_pid = os.path.join(config['run_dir'], 'slapgrid-sr.pid')
  if not os.path.exists(config['software_root']):
    os.mkdir(config['software_root'])
  stopProxy(config)
  removeProxyDb(config)
  startProxy(config)
  logfile = open(config['software_log'], 'w')
  if not updateProxy(config):
    return False
  # Accelerate compilation by setting make -jX
  # XXX-Marco can have issues with implicit dependencies or recursive makefiles. should be configurable.
  environment = os.environ.copy()
  environment['MAKEFLAGS'] = '-j%r' % multiprocessing.cpu_count()
  slapgrid = Popen([config['slapgrid_sr'], '-vc',
                    '--pidfile', slapgrid_pid,
                    config['configuration_file_path'], '--now', '--develop'],
                   stdout=logfile, env=environment,
                   name='slapgrid-sr')
  slapgrid.wait()
  #Saves the current compile software for re-use
  config_SR_folder(config)
  return True


def config_SR_folder(config):
  """Create a symbolik link for each folder in software folder. That allows
    the user to customize software release folder"""
  list = []
  # XXX-Marco do not shadow 'list'
  config_name = 'slaprunner.config'
  for path in os.listdir(config['software_link']):
    cfg_path = os.path.join(config['software_link'], path, config_name)
    if os.path.exists(cfg_path):
      cfg = open(cfg_path).read().split("#")
      if len(cfg) != 2:
        continue  # there is a broken config file
      list.append(cfg[1])
  folder_list = os.listdir(config['software_root'])
  if not folder_list:
    return
  current_project = open(os.path.join(config['etc_dir'], ".project")).read()
  projects = current_project.split('/')
  name = projects[-2]
  for folder in folder_list:
    if folder in list:
      continue  # this folder is already registered
    else:
      if not os.path.exists(os.path.join(config['software_link'], name)):
        destination = os.path.join(config['software_link'], name)
      else:
        destination = os.path.join(config['software_link'], folder)
      source = os.path.join(config['software_root'], folder)
      cfg = os.path.join(destination, config_name)
      #create symlink
      os.symlink(source, destination)
      #write config file
      with open(cfg, 'w') as cf:
        cf.write(current_project + '#' + folder)


def loadSoftwareRList(config):
  """Return list (of dict) of Software Release from symbolik SR folder"""
  list = []
  config_name = 'slaprunner.config'
  for path in os.listdir(config['software_link']):
    cfg_path = os.path.join(config['software_link'], path, config_name)
    if os.path.exists(cfg_path):
      cfg = open(cfg_path).read().split("#")
      if len(cfg) != 2:
        continue  # there is a broken config file
      list.append(dict(md5=cfg[1], path=cfg[0], title=path))
  return list


def isInstanceRunning(config=None):
  """
    Return True if slapgrid-cp is still running and False otherwise
  """
  # XXX-Marco what is 'config' for?
  return isRunning('slapgrid-cp')


def runInstanceWithLock(config):
  """
    Use Slapgrid to deploy current Software Release and wait until
    deployment is done.
  """
  if isInstanceRunning():
    return False

  slapgrid_pid = os.path.join(config['run_dir'], 'slapgrid-cp.pid')
  startProxy(config)
  logfile = open(config['instance_log'], 'w')
  if not (updateProxy(config) and requestInstance(config)):
    return False
  slapgrid = Popen([config['slapgrid_cp'], '-vc',
                    '--pidfile', slapgrid_pid,
                    config['configuration_file_path'], '--now'],
                   stdout=logfile, name='slapgrid-cp')
  slapgrid.wait()
  return True


def getProfilePath(projectDir, profile):
  """
  Return the path of the current Software Release `profile`

  Args:
    projectDir: Slaprunner workspace location.
    profile: file to search into the workspace.

  Returns:
    String, path of current Software Release profile
  """
  if not os.path.exists(os.path.join(projectDir, ".project")):
    return False
  projectFolder = open(os.path.join(projectDir, ".project")).read()
  return os.path.join(projectFolder, profile)


def getSlapStatus(config):
  """Return all Slapos Partitions with associate information"""
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
  if partition_list:
    for i in xrange(0, int(config['partition_amount'])):
      slappart_id = '%s%s' % ("slappart", i)
      if not [x[0] for x in partition_list if slappart_id == x[0]]:
        partition_list.append((slappart_id, []))
  return partition_list


def svcStopAll(config):
  """Stop all Instance process on this computer"""
  return Popen([config['supervisor'], config['configuration_file_path'],
                'shutdown']).communicate()[0]


def removeInstanceRoot(config):
  """Clean instance directory and stop all its running process"""
  if os.path.exists(config['instance_root']):
    svcStopAll(config)
    for root, dirs, _ in os.walk(config['instance_root']):
      for fname in dirs:
        fullPath = os.path.join(root, fname)
        if not os.access(fullPath, os.W_OK):
          # Some directories may be read-only, preventing to remove files in it
          os.chmod(fullPath, 0744)
    shutil.rmtree(config['instance_root'])


def getSvcStatus(config):
  """Return all Softwares Instances process Information"""
  result = Popen([config['supervisor'], config['configuration_file_path'],
                  'status']).communicate()[0]
  regex = "(^unix:.+\.socket)|(^error:)|(^watchdog).*$"
  supervisord = []
  for item in result.split('\n'):
    if item.strip() != "":
      if re.search(regex, item, re.IGNORECASE) is None:
        supervisord.append(re.split('[\s,]+', item))
  return supervisord


def getSvcTailProcess(config, process):
  """Get log for the specifie process

  Args:
    config: Slaprunner configuration
    process: process name. this value is pass to supervisord.
  Returns:
    a string that contains the log of the process.
  """
  return Popen([config['supervisor'], config['configuration_file_path'],
                "tail", process]).communicate()[0]


def svcStartStopProcess(config, process, action):
  """Send start or stop process command to supervisord

  Args:
    config: Slaprunner configuration.
    process: process to start or stop.
    action: current state which is used to generate the new process state.
  """
  cmd = {
    'RESTART': 'restart',
    'STOPPED': 'start',
    'RUNNING': 'stop',
    'EXITED': 'start',
    'STOP': 'stop'
  }
  return Popen([config['supervisor'], config['configuration_file_path'],
                cmd[action], process]).communicate()[0]


def getFolderContent(config, folder):
  """
  Read all file and folder into specified directory

  Args:
    config: Slaprunner configuration.
    folder: the directory to read.

  Returns:
    Html formated string or error message when fail.
  """
  r = ['<ul class="jqueryFileTree" style="display: none;">']
  try:
    folder = str(folder)
    r = ['<ul class="jqueryFileTree" style="display: none;">']
    d = urllib.unquote(folder)
    realdir = realpath(config, d)
    if realdir:
      ldir = sorted(os.listdir(realdir), key=str.lower)
    else:
      r.append('Could not load directory: Permission denied')
      ldir = []

    for f in ldir:
      if f.startswith('.'):  # do not displays this file/folder
        continue
      ff = os.path.join(d, f)
      if os.path.isdir(os.path.join(realdir, f)):
        r.append('<li class="directory collapsed"><a href="#%s" rel="%s/">%s</a></li>' % (ff, ff, f))
      else:
        e = os.path.splitext(f)[1][1:]  # get .ext and remove dot
        r.append('<li class="file ext_%s"><a href="#%s" rel="%s">%s</a></li>' % (e, ff, ff, f))
    r.append('</ul>')
  except Exception as e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))


def getFolder(config, folder):
  """
  Read list of folder for the specified directory

  Args:
    config: Slaprunner configuration.
    folder: the directory to read.

  Returns:
    Html formated string or error message when fail.
  """
  r = ['<ul class="jqueryFileTree" style="display: none;">']
  try:
    folder = str(folder)
    r = ['<ul class="jqueryFileTree" style="display: none;">']
    d = urllib.unquote(folder)
    realdir = realpath(config, d)
    if not realdir:
      r.append('Could not load directory: Permission denied')
      ldir = []
    else:
      ldir = sorted(os.listdir(realdir), key=str.lower)
    for f in ldir:
      if f.startswith('.'):  # do not display this file/folder
        continue
      ff = os.path.join(d, f)
      if os.path.isdir(os.path.join(realdir, f)):
        r.append('<li class="directory collapsed"><a href="#%s" rel="%s/">%s</a></li>' % (ff, ff, f))
    r.append('</ul>')
  except Exception as e:
    r.append('Could not load directory: %s' % str(e))
  r.append('</ul>')
  return jsonify(result=''.join(r))


def getProjectList(folder):
  """Return the list of projet (folder) into the workspace

  Agrs:
    folder: path of the workspace
  Returns:
    a list that contains each folder name.
  """
  project = []
  project_list = sorted(os.listdir(folder), key=str.lower)
  for elt in project_list:
    if os.path.isdir(os.path.join(folder, elt)):
      project.append(elt)
  return project


def configNewSR(config, projectpath):
  """Configure a Software Release as current Software Release

  Args:
    config: slaprunner configuration
    projectpath: path of the directory that contains the software realease to configure
  Returns:
    True if all is done well, otherwise return false.
  """
  folder = realpath(config, projectpath)
  if folder:
    if isInstanceRunning():
      killRunningProcess('slapgrid-cp')
    if isSoftwareRunning():
      killRunningProcess('slapgrid-sr')
    stopProxy(config)
    removeProxyDb(config)
    startProxy(config)
    removeInstanceRoot(config)
    param_path = os.path.join(config['etc_dir'], ".parameter.xml")
    if os.path.exists(param_path):
      os.remove(param_path)
    open(os.path.join(config['etc_dir'], ".project"), 'w').write(projectpath)
    return True
  else:
    return False


def newSoftware(folder, config, session):
  """
  Create a new Software Release folder with default profiles

  Args:
    folder: directory of the new software release
    config: slraprunner configuration
    session: Flask session directory"""
  json = ""
  code = 0
  basedir = config['etc_dir']
  try:
    folderPath = realpath(config, folder, check_exist=False)
    if folderPath and not os.path.exists(folderPath):
      os.mkdir(folderPath)
      #load software.cfg and instance.cfg from http://git.erp5.org
      software = "http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/lamp-template/software.cfg"
      softwareContent = ""
      try:
        softwareContent = urllib.urlopen(software).read()
      except:
        #Software.cfg and instance.cfg content will be empty
        pass
      open(os.path.join(folderPath, config['software_profile']), 'w').write(softwareContent)
      open(os.path.join(folderPath, config['instance_profile']), 'w').write("")
      open(os.path.join(basedir, ".project"), 'w').write(folder + "/")
      #Clean sapproxy Database
      stopProxy(config)
      removeProxyDb(config)
      startProxy(config)
      #Stop runngin process and remove existing instance
      removeInstanceRoot(config)
      session['title'] = getProjectTitle(config)
      code = 1
    else:
      json = "Bad folder or Directory '%s' already exist, please enter a new name for your software" % folder
  except Exception as e:
    json = "Can not create your software, please try again! : %s " % e
    if os.path.exists(folderPath):
      shutil.rmtree(folderPath)
  return jsonify(code=code, result=json)


def checkSoftwareFolder(path, config):
  """Check id `path` is a valid Software Release folder"""
  realdir = realpath(config, path)
  if realdir and os.path.exists(os.path.join(realdir, config['software_profile'])):
    return jsonify(result=path)
  return jsonify(result="")


def getProjectTitle(config):
  """Generate the name of the current software Release (for slaprunner UI)"""
  conf = os.path.join(config['etc_dir'], ".project")
  if os.path.exists(conf):
    project = open(conf, "r").read().split("/")
    software = project[-2]
    return '%s (%s)' % (software, '/'.join(project[:-2]))
  return "No Profile"


def getSoftwareReleaseName(config):
  """Get the name of the current Software Release"""
  sr_profile = os.path.join(config['etc_dir'], ".project")
  if os.path.exists(sr_profile):
    project = open(sr_profile, "r").read().split("/")
    software = project[-2]
    return software.replace(' ', '_')
  return "No_name"


def removeSoftwareByName(config, md5, folderName):
  """Remove all content of the software release specified by md5

  Args:
    config: slaprunner configuration
    foldername: the link name given to the software release
    md5: the md5 filename given by slapgrid to SR folder"""
  if isSoftwareRunning() or isInstanceRunning():
    raise Exception("Software installation or instantiation in progress, cannot remove")
  path = os.path.join(config['software_root'], md5)
  linkpath = os.path.join(config['software_link'], folderName)
  if not os.path.exists(path):
    raise Exception("Cannot remove software Release: No such file or directory")
  if not os.path.exists(linkpath):
    raise Exception("Cannot remove software Release: No such file or directory %s" %
                    ('software_root/' + folderName))
  svcStopAll(config)
  os.unlink(linkpath)
  shutil.rmtree(path)
  return loadSoftwareRList(config)


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
          f.seek(0, 0)
          # only read what was not read
          data.insert(0, f.read(bytes))
      linesFound = data[0].count('\n')
      size -= linesFound
      bytes -= BUFSIZ
      block -= 1
  return '\n'.join(''.join(data).splitlines()[-lines:])


def readFileFrom(f, lastPosition, limit=20000):
  """
  Returns the last lines of file `f`, from position lastPosition.
  and the last position
  limit = max number of caracter to read
  """
  BUFSIZ = 1024
  f.seek(0, 2)
  # XXX-Marco do now shadow 'bytes'
  bytes = f.tell()
  block = -1
  data = ""
  length = bytes
  truncated = False  # True if a part of log data has been truncated
  if (lastPosition <= 0 and length > limit) or (length - lastPosition > limit):
    lastPosition = length - limit
    truncated = True
  size = bytes - lastPosition
  while bytes > lastPosition:
    if abs(block * BUFSIZ) <= size:
      # Seek back one whole BUFSIZ
      f.seek(block * BUFSIZ, 2)
      data = f.read(BUFSIZ) + data
    else:
      margin = abs(block * BUFSIZ) - size
      if length < BUFSIZ:
        f.seek(0, 0)
      else:
        seek = block * BUFSIZ + margin
        f.seek(seek, 2)
      data = f.read(BUFSIZ - margin) + data
    bytes -= BUFSIZ
    block -= 1
  f.close()
  return {
    'content': data,
    'position': length,
    'truncated': truncated
  }


def isText(file):
  """Return True if the mimetype of file is Text"""
  if not os.path.exists(file):
    return False
  text_range = ''.join(map(chr, [7, 8, 9, 10, 12, 13, 27] + range(0x20, 0x100)))
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
    m = md5.md5()
    while True:
      data = fh.read(8192)
      if not data:
        break
      m.update(data)
    return m.hexdigest()
  except:
    return False


def realpath(config, path, check_exist=True):
  """
  Get realpath of path or return False if user is not allowed to access to
  this file.
  """
  split_path = path.split('/')
  key = split_path[0]
  allow_list = {
    'software_root': config['software_root'],
    'instance_root': config['instance_root'],
    'workspace': config['workspace'],
    'software_link': config['software_link']
  }
  if key not in allow_list:
    return False

  del split_path[0]
  path = os.path.join(allow_list[key], *split_path)
  if check_exist:
    if os.path.exists(path):
      return path
    else:
      return False
  else:
    return path


def readParameters(path):
  """Read Instance parameters stored into a local file.

  Agrs:
    path: path of the xml file that contains parameters

  Return:
    a dictionary of instance parameters."""
  if os.path.exists(path):
    try:
      xmldoc = minidom.parse(path)
      obj = {}
      for elt in xmldoc.childNodes:
        sub_obj = {}
        for subnode in elt.childNodes:
          if subnode.nodeType != subnode.TEXT_NODE:
            sub_obj[str(subnode.getAttribute('id'))] = subnode.childNodes[0].data  # .decode('utf-8').decode('utf-8')
            obj[str(elt.tagName)] = sub_obj
      return obj
    except Exception, e:
      return str(e)
  else:
    return "No such file or directory: %s" % path
