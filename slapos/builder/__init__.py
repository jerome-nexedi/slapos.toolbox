# -*- coding: utf-8 -*-
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
import os
import sys
from optparse import OptionParser, Option
from subprocess import call as subprocessCall
from stat import S_ISBLK, ST_MODE
from tempfile import mkdtemp, mkstemp
import shutil
import pkg_resources

class SlapError(Exception):
  """
  Slap error
  """
  def __init__(self, message):
    self.msg = message

class UsageError(SlapError):
  pass

class ExecError(SlapError):
  pass

def rootRightsNeeded(func):
  "Decorator for permissions checking"
  def wrapped(*args, **kwargs):
    if os.getuid() != 0:
      raise UsageError("You need to be root to run this script !")
    return func(*args, **kwargs)
  return wrapped

def _call(cmd_args, stdout=None, stderr=None, dry_run=False):
  """
  Wrapper for subprocess.call() which'll secure the usage of external program's.

  Args:
    cmd_args: list of strings representing the command and all it's needed args
    stdout/stderr: only precise PIPE (from subprocess) if you don't want the
        command to create output on the regular stream
  """
  print "Calling: %s" % ' '.join(cmd_args)
  if not dry_run:
    try:
      if subprocessCall(cmd_args, stdout=stdout, stderr=stderr) != 0:
        raise ValueError('Issues during running %r' % cmd_args)
    except OSError as e:
      raise ExecError('Process respond:"%s" when calling "%s"' % \
                      (str(e), ' '.join(cmd_args)))

class Parser(OptionParser):
  """
  Parse all arguments.
  """
  def __init__(self, usage=None, version=None):
    """
    Initialize all options possibles.
    """
    OptionParser.__init__(self, usage=usage, version=version,
                          option_list=[
      Option("-c", "--slapos_configuration",
             help="The path of the slapos configuration directory",
             default='/etc/slapos/',
             type=str),
      Option("-o", "--hostname_path",
             help="The hostname configuration path",
             default='/etc/HOSTNAME',
             type=str),
      Option("-s", "--host_path",
             help="The hosts configuration path",
             default='/etc/hosts',
             type=str),
      Option("-n", "--dry_run",
             help="Simulate the execution steps",
             default=False,
             action="store_true"),
      Option(None, "--no_usb", default=False, action="store_true",
        help="Do not write on USB."),
      Option(None, "--one_disk",default=False, action="store_true",
             help="Prepare image for one disk usage"),
      Option(None, "--virtual",default=False, action="store_true",
             help="Work with .vmdk files")
   ])

  def check_args(self):
    """
    Check arguments
    """
    (options, args) = self.parse_args()
    if len(args) != 8:
      self.error("Incorrect number of arguments")
    system_path, device_path, computer_id, key_path, master_url, \
        slapos_software_profile_url, cert_file, key_file = args

    system_path = os.path.abspath(system_path)
    if not os.path.isfile(system_path):
      self.error("%s isn't valid. The first argument must be the raw " \
                 "slapos file" % system_path)

    if options.virtual:
      options.no_usb=True
      options.one_disk=True

    device_path = os.path.abspath(device_path)
    if not options.no_usb:
      mode = os.stat(device_path)[ST_MODE]
      if not S_ISBLK(mode):
        self.error("%s isn't a valid block file. Please enter as second " \
                 "argument a valid block file for the raw to be copied on " \
                 "it" % device_path)

    if not os.path.isfile(key_path):
      self.error("%r file not found" % key_path)

    return options, system_path, device_path, computer_id, key_path,\
        master_url, slapos_software_profile_url, cert_file, key_file

@rootRightsNeeded
def run(config):
  dry_run = config.dry_run
  print "Creating temp directory"
  if not dry_run:
    mount_dir_path = mkdtemp()
    fdisk_output_path = mkstemp()[1]
  else:
    mount_dir_path = "/tmp/a_generated_directory"
    fdisk_output_path = "/tmp/a_generated_file"
  try:
    if not config.virtual:
    	offset = 0
    	fdisk_output_file = open(fdisk_output_path, 'w')
    	_call(['sfdisk', '-d', '-uS', config.system_path], stdout=fdisk_output_file)
    	fdisk_output_file.close()
    	fdisk_output_file = open(fdisk_output_path, 'r')
    	for line in fdisk_output_file:
    	  line = line.rstrip().replace(' ', '')
    	  if line.endswith("bootable"):
    	    offset = int(line.split(':')[1].split(',')[0].split('=')[1])
    	fdisk_output_file.close()
    	offset = offset * 512
    	_call(['mount', '-o', 'loop,offset=%i' % offset, config.system_path,
    	       mount_dir_path], dry_run=dry_run)
    # Call vmware-mount to mount Virtual disk image
    else:
      print "Mount Virtual Image"
      fdisk_output_file = open(fdisk_output_path, 'w')
      _call(['vmware-mount', config.system_path, mount_dir_path], dry_run=dry_run )      
  
    try:
      # Create slapos configuration directory if needed
      slap_configuration_directory = os.path.normpath('/'.join([mount_dir_path,
                                              config.slapos_configuration]))
      slap_configuration_file = os.path.normpath('/'.join([
        slap_configuration_directory, 'slapos.cfg']))
      if not os.path.exists(slap_configuration_directory):
        print "Creating directory: %s" % slap_configuration_directory
        if not dry_run:
          os.mkdir(slap_configuration_directory, 0711)

      certificate_repository_path = os.path.join('/opt/slapos/pki')
      key_file = os.path.join(config.slapos_configuration, 'computer.key')
      cert_file = os.path.join(config.slapos_configuration, 'computer.crt')
      key_file_dest = os.path.normpath('/'.join([mount_dir_path,
                                              key_file]))
      cert_file_dest = os.path.normpath('/'.join([mount_dir_path,
                                              cert_file]))
      for (src, dst) in [(config.key_file, key_file_dest), (config.cert_file,
        cert_file_dest)]:
        print "Coping %r to %r, and setting minimum privileges" % (src, dst)
        if not dry_run:
          shutil.copy(src, dst)
          os.chmod(dst, 0600)
          os.chown(dst, 0, 0)

      # Put slapgrid configuration file
      print "Creating slap configuration: %s" % slap_configuration_file
      if not dry_run:
        open(slap_configuration_file, 'w').write(
          pkg_resources.resource_stream(__name__,
            'template/slapos.cfg.in').read() % dict(
              computer_id=config.computer_id, master_url=config.master_url,
              key_file=key_file, cert_file=cert_file,
              certificate_repository_path=certificate_repository_path
            ))

      hostname_path = os.path.normpath('/'.join([mount_dir_path,
                                              config.hostname_path]))
      print "Setting hostname in : %s" % hostname_path
      if not dry_run:
        open(hostname_path, 'w').write("%s\n" % config.computer_id)

      # Adding the hostname as a valid address 
      host_path = os.path.normpath('/'.join([mount_dir_path,
                                             config.host_path]))
      print "Creating %r" % host_path
      if not dry_run:
        open(host_path, 'w').write(
          pkg_resources.resource_stream(__name__,
            'template/hosts.in').read() % dict(
              computer_id=config.computer_id))

      # Creating safe sshd_config
      sshd_path = os.path.normpath('/'.join([mount_dir_path, 'etc', 'ssh',
        'sshd_config']))
      print "Creating %r" % sshd_path
      if not dry_run:
        open(sshd_path, 'w').write(
          pkg_resources.resource_stream(__name__,
            'template/sshd_config.in').read())
        os.chmod(sshd_path, 0600)

      # Creating default bridge config
      br0_path = os.path.normpath('/'.join([mount_dir_path, 'etc',
        'sysconfig', 'network', 'ifcfg-br0']))
      print "Creating %r" % br0_path
      if not dry_run:
        open(br0_path, 'w').write(
          pkg_resources.resource_stream(__name__,
            'template/ifcfg-br0.in').read())

      # Writing ssh key

      user_path = os.path.normpath('/'.join([mount_dir_path, 'root']))
      ssh_key_directory = os.path.normpath('/'.join([user_path, '.ssh']))
      ssh_key_path = os.path.normpath('/'.join([ssh_key_directory,
        'authorized_keys']))
      stat_info = os.stat(user_path)
      uid, gid = stat_info.st_uid, stat_info.st_gid
      ssh_key_directory = os.path.dirname(ssh_key_path)
      if not os.path.exists(ssh_key_directory):
        print "Creating ssh directory: %s" % ssh_key_directory
        if not dry_run:
          os.mkdir(ssh_key_directory)
      if not dry_run:
        print "Setting uid:gid of %r to %s:%s" % (ssh_key_directory, uid, gid)
        os.chown(ssh_key_directory, uid, gid)
        os.chmod(ssh_key_directory, 0700)

      print "Creating file: %s" % ssh_key_path
      if not dry_run:
        shutil.copyfile(config.key_path, ssh_key_path)

      if not dry_run:
        print "Setting uid:gid of %r to %s:%s" % (ssh_key_path, uid, gid)
        os.chown(ssh_key_path, uid, gid)
        os.chmod(ssh_key_path, 0600)

      # slapos buildout profile
      slapos_software_file = os.path.normpath('/'.join([mount_dir_path,
                                              config.slapos_configuration,
                                              'software.cfg']))
      print "Creating slapos software profile: %s" % slapos_software_file
      if not dry_run:
        open(slapos_software_file, 'w').write('[buildout]\nextends = %s' %
            config.slapos_software_profile_url)
        os.chmod(slapos_software_file, 0644)

      # Creating boot scripts
      path = os.path.join(mount_dir_path, 'etc', 'slapos', 'slapos')
      print "Creating %r" % path
      if not dry_run:
        open(path, 'w').write(pkg_resources.resource_stream(__name__,
          'script/%s' % 'slapos').read())
        os.chmod(path, 0755)
      path = os.path.join(mount_dir_path, 'etc', 'systemd', 'system','slapos.service')
      print "Creating %r" % path
      if not dry_run:
        open(path, 'w').write(pkg_resources.resource_stream(__name__,
          'script/%s' % 'slapos.service').read())
        os.chmod(path, 0755)
          
      # Removing line in slapos script activating kvm in virtual 
      if config.virtual:
        path = os.path.join(mount_dir_path, 'etc', 'slapos','slapos')
        _call(['sed','-i',"$d",path],dry_run=dry_run)
        _call(['sed','-i',"$d",path],dry_run=dry_run)
        
      # Adding slapos_firstboot in case of MultiDisk usage    
      if not config.one_disk :
      	for script in ['slapos_firstboot']:
      	  path = os.path.join(mount_dir_path, 'etc', 'init.d', script)
      	  print "Creating %r" % path
      	  if not dry_run:
      	    open(path, 'w').write(pkg_resources.resource_stream(__name__,
      	      'script/%s' % script).read())
      	    os.chmod(path, 0755)	  
      else:
        for script in ['slapos_firstboot']:
      	  path = os.path.join(mount_dir_path, 'etc', 'init.d', script)
          if os.path.exists(path):
            print "Removing %r" % path
            os.remove(path)
      

    finally:
      if not config.virtual:
        _call(['umount', mount_dir_path], dry_run=dry_run)
      else:
        print "Umount Virtual Machine"
        _call(["vmware-mount","-K",config.system_path],dry_run=dry_run)
  finally:
    # Always delete temporary directory
    #print "No deleting"
    print "Deleting temp directory: %s" % mount_dir_path
    if not dry_run:
      shutil.rmtree(mount_dir_path)
      print "Deleting temp file: %s" % fdisk_output_path
    if not dry_run:
      os.remove(fdisk_output_path)
       
  # Copying
  if not config.no_usb:
    print "\nStarting the copy of the raw file, it may take some time...\n"
    _call(['dd', "if=%s" % config.system_path, "of=%s" % config.device_path], dry_run=dry_run)
    _call(['sync'])
    print "\n... copy finished! You may now take the usb key back."

  return 0

class Config:
  def setConfig(self, option_dict, system_path, device_path, computer_id,
                key_path, master_url, slapos_software_profile_url, cert_file,
                key_file):
    """
    Set options given by parameters.
    """
    # Set options parameters
    for option, value in option_dict.__dict__.items():
      setattr(self, option, value)
    self.system_path = system_path
    self.device_path = device_path
    self.computer_id = computer_id
    self.key_path = key_path
    self.master_url = master_url
    self.slapos_software_profile_url = slapos_software_profile_url
    self.key_file = key_file
    self.cert_file = cert_file

def main():
  "Run default configuration."
  usage = "usage: %s [options] SYSTEM_FILE OUTPUT_DEVICE " \
          "COMPUTER_ID SSH_KEY_FILE MASTER_URL SLAPOS_SOFTWARE_PROFILE_URL "\
          "COMPUTER_CERTIFICATE COMPUTER_KEY" % sys.argv[0]

  try:
    # Parse arguments
    config = Config()
    config.setConfig(*Parser(usage=usage).check_args())

    run(config)
    return_code = 0
  except UsageError, err:
    print >>sys.stderr, err.msg
    print >>sys.stderr, "For help use --help"
    return_code = 16
  except ExecError, err:
    print >>sys.stderr, err.msg
    return_code = 16
  except SystemExit, err:
    # Catch exception raise by optparse
    return_code = err

  sys.exit(return_code)
