# -*- coding: utf-8 -*-
import os
import sys
import views
import unittest
import tempfile
from optparse import OptionParser, Option
import ConfigParser
import shutil
from gittools import cloneRepo, gitStatus, switchBranch, addBranch, getDiff, \
     gitPush, gitPull
from flaskext.auth import Auth, AuthUser, login_required, logout
from utils import *
import json
from datetime import timedelta

class Config:
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
    #create slaprunner configuration
    config = Config()
    config.setConfig()
    workdir = os.path.join(config.runner_workdir, 'project')
    views.app.config.update(**config.__dict__)
    #update or create all runner base directory to test_dir
    if not os.path.exists(workdir):
      os.mkdir(workdir)
    views.app.config.update(
      software_log=config.software_root.rstrip('/') + '.log',
      instance_log=config.instance_root.rstrip('/') + '.log',
      workspace = workdir,
      instance_profile='instance.cfg',
      software_profile='software.cfg',
      SECRET_KEY="123456",
      PERMANENT_SESSION_LIFETIME=timedelta(days=31),
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
    sr_data = project = os.path.join(self.app.config['etc_dir'], '.softdata')
    proxy = os.path.join(self.app.config['etc_dir'], '.proxy.pid')
    slapgrid_cp = os.path.join(self.app.config['etc_dir'], '.slapgrid-cp.pid')
    slapgrid_sr = os.path.join(self.app.config['etc_dir'], '.slapgrid-sr.pid')
    users = os.path.join(self.app.config['etc_dir'], '.users')
    if os.path.exists(users):
      os.unlink(users)
    if os.path.exists(project):
      os.unlink(project)
    if os.path.exists(sr_data):
      os.unlink(sr_data)
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


  #Helpers
  def loadJson(self, response):
    return json.loads(response.data)

  def configAccount(self, username, password, email, name, rcode):
    """Helper for configAccoun"""
    return self.app.post('/configAccount', data=dict(
            username=username,
            password=password,
            email=email,
            name=name,
            rcode=rcode
          ), follow_redirects=True)
  def configAccount(self, username, password, email, name, rcode):
    """Helper for configAccoun"""
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
    response = self.loadJson(self.configAccount(self.users[0], self.users[1],
                  self.users[2], self.users[3], self.rcode))
    response2 = self.loadJson(self.login(self.users[0], self.users[1]))
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
    response = self.loadJson(result)
    self.assertEqual(response['code'], 1)
    account = getSession(self.app.config)
    self.assertEqual(account, self.users)

  def test_login_logout(self):
    """test login with good and wrong values, test logout"""
    response = self.loadJson(self.configAccount(self.users[0], self.users[1],
                  self.users[2], self.users[3], self.rcode))
    self.assertEqual(response['result'], "")
    result = self.loadJson(self.login(self.users[0], "wrongpwd"))
    self.assertEqual(result['result'], "Login or password is incorrect, please check it!")
    resultwr = self.loadJson(self.login("wronglogin", "wrongpwd"))
    self.assertEqual(resultwr['result'], "Login or password is incorrect, please check it!")
    #try now with true values
    resultlg = self.loadJson(self.login(self.users[0], self.users[1]))
    self.assertEqual(resultlg['result'], "")
    #after login test logout
    result = self.logout()
    assert "<h2>Login to Slapos Web Runner</h2>" in result.data

  def test_updateAccount(self):
    """test Update accound, this need user to loging in"""
    self.setAccount()
    response = self.loadJson(self.updateAccount(self.updateUser, self.rcode))
    self.assertEqual(response['code'], 1)
    result = self.logout()
    assert "<h2>Login to Slapos Web Runner</h2>" in result.data
    #retry login with new values
    response = self.loadJson(self.login(self.updateUser[0], self.updateUser[1]))
    self.assertEqual(response['result'], "")
    #log out now!
    self.logout()


def main():
  argv = ['', 'test_wrong_login', 'test_configAccount',
          'test_login_logout', 'test_updateAccount']
  unittest.main(module=SlaprunnerTestCase, argv=argv)

if __name__ == '__main__':
  main()