# -*- coding: utf-8 -*-
# vim: set et sts=2:
# pylint: disable-msg=W0311,C0301,C0103,C0111,R0904

import ConfigParser
import datetime
import json
import os
import shutil
import unittest

from slapos.runner.utils import (getProfilePath, getSession, isInstanceRunning, isSoftwareRunning, readPid,
                                 recursifKill, startProxy)
from slapos.runner import views

#Helpers
def loadJson(response):
  return json.loads(response.data)


class Config:
  def __init__(self):
    self.runner_workdir = None
    self.software_root = None
    self.instance_root = None
    self.configuration_file_path = None

  def setConfig(self):
    """
    Set options given by parameters.
    """
    self.configuration_file_path = os.path.abspath(os.environ.get('CONFIG_FILE_PATH'))

    # Load configuration file
    configuration_parser = ConfigParser.SafeConfigParser()
    configuration_parser.read(self.configuration_file_path)
    # Merges the arguments and configuration

    for section in ("slaprunner", "slapos", "slapproxy", "slapformat",
                    "sshkeys_authority", "gitclient", "cloud9_IDE"):
      configuration_dict = dict(configuration_parser.items(section))
      for key in configuration_dict:
        if not getattr(self, key, None):
          setattr(self, key, configuration_dict[key])

class SlaprunnerTestCase(unittest.TestCase):

  def setUp(self):
    """Initialize slapos webrunner here"""
    views.app.config['TESTING'] = True
    self.users = ["slapuser", "slappwd", "slaprunner@nexedi.com", "SlapOS web runner"]
    self.updateUser = ["newslapuser", "newslappwd", "slaprunner@nexedi.com", "SlapOS web runner"]
    self.rcode = "41bf2657"
    self.repo = 'http://git.erp5.org/repos/slapos.git'
    self.software = "workspace/slapos/software/" #relative directory fo SR
    self.project = 'slapos' #Default project name
    #create slaprunner configuration
    config = Config()
    config.setConfig()
    workdir = os.path.join(config.runner_workdir, 'project')
    software_link = os.path.join(config.runner_workdir, 'softwareLink')
    views.app.config.update(**config.__dict__)
    #update or create all runner base directory to test_dir

    if not os.path.exists(workdir):
      os.mkdir(workdir)
    views.app.config.update(
      software_log=config.software_root.rstrip('/') + '.log',
      instance_log=config.instance_root.rstrip('/') + '.log',
      workspace = workdir,
      software_link=software_link,
      instance_profile='instance.cfg',
      software_profile='software.cfg',
      SECRET_KEY="123456",
      PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=31),
    )
    self.app = views.app.test_client()
    self.app.config = views.app.config
    #Create password recover code
    rpwd = open(os.path.join(views.app.config['etc_dir'], '.rcode'), 'w')
    rpwd.write(self.rcode)
    rpwd.close()

  def tearDown(self):
    """Remove all test data"""
    os.unlink(os.path.join(self.app.config['etc_dir'], '.rcode'))
    project = os.path.join(self.app.config['etc_dir'], '.project')
    proxy = os.path.join(self.app.config['run_dir'], 'proxy.pid')
    slapgrid_cp = os.path.join(self.app.config['run_dir'], 'slapgrid-cp.pid')
    slapgrid_sr = os.path.join(self.app.config['run_dir'], 'slapgrid-sr.pid')
    users = os.path.join(self.app.config['etc_dir'], '.users')
    #Stop process
    #self.stopSlapproxy()
    if os.path.exists(users):
      os.unlink(users)
    if os.path.exists(project):
      os.unlink(project)
    if os.path.exists(proxy):
      os.unlink(proxy)
    if os.path.exists(slapgrid_cp):
      os.unlink(slapgrid_cp)
    if os.path.exists(slapgrid_sr):
      os.unlink(slapgrid_sr)
    if os.path.exists(self.app.config['workspace']):
      shutil.rmtree(self.app.config['workspace'])
    if os.path.exists(self.app.config['software_root']):
      shutil.rmtree(self.app.config['software_root'])
    if os.path.exists(self.app.config['instance_root']):
      shutil.rmtree(self.app.config['instance_root'])

  def configAccount(self, username, password, email, name, rcode):
    """Helper for configAccount"""
    return self.app.post('/configAccount', data=dict(
            username=username,
            password=password,
            email=email,
            name=name,
            rcode=rcode
          ), follow_redirects=True)

  def login(self, username, password):
    """Helper for Login method"""
    return self.app.post('/doLogin', data=dict(
            clogin=username,
            cpwd=password
          ), follow_redirects=True)

  def setAccount(self):
    """Initialize user account and log user in"""
    response = loadJson(self.configAccount(self.users[0], self.users[1],
                  self.users[2], self.users[3], self.rcode))
    response2 = loadJson(self.login(self.users[0], self.users[1]))
    self.assertEqual(response['result'], "")
    self.assertEqual(response2['result'], "")

  def logout(self):
    """Helper for Logout current user"""
    return self.app.get('/dologout', follow_redirects=True)

  def updateAccount(self, newaccount, rcode):
    """Helper for update user account data"""
    return self.app.post('/updateAccount', data=dict(
            username=newaccount[0],
            password=newaccount[1],
            email=newaccount[2],
            name=newaccount[3],
            rcode=rcode
          ), follow_redirects=True)

  def getCurrentSR(self):
   return getProfilePath(self.app.config['etc_dir'],
                              self.app.config['software_profile'])
  def proxyStatus(self, status=True):
    """Helper for testslapproxy status"""
    proxy_pid = os.path.join(self.app.config['run_dir'], 'proxy.pid')
    pid = readPid(proxy_pid)
    try:
      os.kill(pid, 0)
      proxy = True
    except Exception:
      proxy = False
    self.assertEqual(proxy, status)

  def stopSlapproxy(self):
    """Kill slapproxy process"""
    proxy_pid = os.path.join(self.app.config['run_dir'], 'proxy.pid')
    pid = readPid(proxy_pid)
    recursifKill([pid])

  #Begin test case here
  def test_wrong_login(self):
    """Test Login user before create session. This should return error value"""
    response = self.login(self.users[0], self.users[1])
    #redirect to config account page
    assert "<h2 class='title'>Your personal informations</h2><br/>" in response.data

  def test_configAccount(self):
    """For the first lauch of slaprunner user need do create first account"""
    result = self.configAccount(self.users[0], self.users[1], self.users[2],
                  self.users[3], self.rcode)
    response = loadJson(result)
    self.assertEqual(response['code'], 1)
    account = getSession(self.app.config)
    self.assertEqual(account, self.users)

  def test_login_logout(self):
    """test login with good and wrong values, test logout"""
    response = loadJson(self.configAccount(self.users[0], self.users[1],
                  self.users[2], self.users[3], self.rcode))
    self.assertEqual(response['result'], "")
    result = loadJson(self.login(self.users[0], "wrongpwd"))
    self.assertEqual(result['result'], "Login or password is incorrect, please check it!")
    resultwr = loadJson(self.login("wronglogin", "wrongpwd"))
    self.assertEqual(resultwr['result'], "Login or password is incorrect, please check it!")
    #try now with true values
    resultlg = loadJson(self.login(self.users[0], self.users[1]))
    self.assertEqual(resultlg['result'], "")
    #after login test logout
    result = self.logout()
    assert "<h2>Login to Slapos Web Runner</h2>" in result.data

  def test_updateAccount(self):
    """test Update accound, this need user to loging in"""
    self.setAccount()
    response = loadJson(self.updateAccount(self.updateUser, self.rcode))
    self.assertEqual(response['code'], 1)
    result = self.logout()
    assert "<h2>Login to Slapos Web Runner</h2>" in result.data
    #retry login with new values
    response = loadJson(self.login(self.updateUser[0], self.updateUser[1]))
    self.assertEqual(response['result'], "")
    #log out now!
    self.logout()

  def test_startProxy(self):
    """Test slapproxy"""
    startProxy(self.app.config)
    self.proxyStatus(True)
    self.stopSlapproxy()

  def test_cloneProject(self):
    """Start scenario 1 for deploying SR: Clone a project from git repository"""
    self.setAccount()
    folder = 'workspace/' + self.project
    data = {"repo":self.repo, "user":'Slaprunner test',
          "email":'slaprunner@nexedi.com', "name":folder}
    response = loadJson(self.app.post('/cloneRepository', data=data,
                    follow_redirects=True))
    self.assertEqual(response['result'], "")
    #Get realpath of create project
    path_data = dict(file=folder)
    response = loadJson(self.app.post('/getPath', data=path_data,
                    follow_redirects=True))
    self.assertEqual(response['code'], 1)
    realFolder = response['result'].split('#')[0]
    #Check git configuration
    config = open(os.path.join(realFolder, '.git/config'), 'r').read()
    assert "slaprunner@nexedi.com" in config and "Slaprunner test" in config
    #Checkout to slaprunner branch, this supose that branch slaprunner exit
    response = loadJson(self.app.post('/newBranch', data=dict(
                    project=folder,
                    create='0',
                    name='slaprunner'),
                    follow_redirects=True))
    self.assertEqual(response['result'], "")
    self.logout()

  def test_createSR(self):
    """Scenario 2: Create a new software release"""
    self.test_cloneProject()
    #Login
    self.login(self.users[0], self.users[1])
    #test create SR
    newSoftware = os.path.join(self.software, 'slaprunner-test')
    response = loadJson(self.app.post('/createSoftware',
                    data=dict(folder=newSoftware),
                    follow_redirects=True))
    self.assertEqual(response['result'], "")
    currentSR = self.getCurrentSR()
    assert newSoftware in currentSR
    self.logout()

  def test_openSR(self):
    """Scenario 3: Open software release"""
    self.test_cloneProject()
    #Login
    self.login(self.users[0], self.users[1])
    software = os.path.join(self.software, 'drupal') #Drupal SR must exist in SR folder
    response = loadJson(self.app.post('/setCurrentProject',
                    data=dict(path=software),
                    follow_redirects=True))
    self.assertEqual(response['result'], "")
    currentSR = self.getCurrentSR()
    assert software in currentSR
    self.assertFalse(isInstanceRunning(self.app.config))
    self.assertFalse(isSoftwareRunning(self.app.config))
    #Slapproxy process is supose to be started
    self.proxyStatus(True)
    self.stopSlapproxy()
    self.logout()

def main():
  argv = ['', 'test_wrong_login', 'test_configAccount',
          'test_login_logout', 'test_updateAccount', 'test_startProxy',
          'test_cloneProject', 'test_createSR', 'test_openSR']
  unittest.main(module=SlaprunnerTestCase, argv=argv)

if __name__ == '__main__':
  main()
