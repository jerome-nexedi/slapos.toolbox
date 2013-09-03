# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Vifib SARL and Contributors. All Rights Reserved.
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

from .resiliencytestsuite import ResiliencyTestSuite

import cookielib
import random
import string
import time
import urllib2

class NotHttpOkException(Exception):
  pass

class SlaprunnerTestSuite(ResiliencyTestSuite):
  """
  Run Slaprunner Resiliency Test.
  It is highly suggested to read ResiliencyTestSuite code.
  """
  def __init__(self,
               server_url, key_file, cert_file,
               computer_id, partition_id, software,
               namebase, slaprunner_rootinstance_name,
               total_instance_count="3"):

    # Setup urllib2 with cookie support
    cookie_jar = cookielib.CookieJar()
    self._opener_director = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))

    ResiliencyTestSuite.__init__(
        self,
        server_url, key_file, cert_file,
        computer_id, partition_id, software,
        namebase,
        slaprunner_rootinstance_name
    )

  def generateData(self):
    self.slaprunner_password = ''.join(random.SystemRandom().sample(string.ascii_lowercase, 8))
    self.slaprunner_user = 'slapos'
    self.logger.info('Generated slaprunner user is: %s' % self.slaprunner_user)
    self.logger.info('Generated slaprunner password is: %s' % self.slaprunner_password)

  def _connectToSlaprunner(self, resource, data=None):
    """
    Utility.
    Connect through HTTP to the slaprunner instance.
    Require self.slaprunner_backend_url to be set.
    """
    url = "%s/%s" % (self.slaprunner_backend_url, resource)
    if data:
      result = self._opener_director.open(url, data=data)
    else:
      result = self._opener_director.open(url)

    if result.getcode() is not 200:
      raise NotHttpOkException(result.getcode())
    return result.read()

  def _login(self):
    self.logger.debug('Logging in...')
    self._connectToSlaprunner('doLogin', data='clogin=%s&cpwd=%s' % (self.slaprunner_user, self.slaprunner_password))

  def _retrieveInstanceLogFile(self):
    """
    Store the logfile (=data) of the instance, check it is not empty nor it is html.
    """
    data = self._connectToSlaprunner(resource='fileBrowser', data='opt=9&filename=log.log&dir=instance_root%252Fslappart0%252Fvar%252Flog%252F')
    self.logger.info('Retrieved data are:\n%s' % data)

    if data.find('<') is not -1:
      raise IOError('Could not retrieve logfile content: retrieved content is html.')
    if data.find('Could not load') is not -1:
      raise IOError('Could not retrieve logfile content: server could not load the file.')
    if data.find('Hello') is -1:
      raise IOError('Could not retrieve logfile content: retrieve content does not match "Hello".')
    return data

  def pushDataOnMainInstance(self):
    """
    Create a dummy Software Release,
    Build it,
    Wait for build to be successful,
    Deploy instance,
    Wait for instance to be started.
    Store the main IP of the slaprunner for future use.
    """
    self.logger.debug('Getting the backend URL and recovery code...')
    parameter_dict = self._getPartitionParameterDict()
    self.slaprunner_backend_url = parameter_dict['backend_url']
    self.logger.info('backend_url is %s.' % self.slaprunner_backend_url)
    slaprunner_recovery_code = parameter_dict['password_recovery_code']

    self.logger.debug('Creating the slaprunner account...')
    self._connectToSlaprunner(resource='configAccount', data='name=slapos&username=%s&email=slapos@slapos.org&password=%s&rcode=%s' % (self.slaprunner_user, self.slaprunner_password, slaprunner_recovery_code))

    self._login()

    self.logger.debug('Opening hello-world software release from git...')
    try:
      self._connectToSlaprunner(resource='cloneRepository', data='repo=http://git.erp5.org/repos/slapos.git&name=workspace/slapos&email=slapos@slapos.org&user=slapos')
    except (NotHttpOkException, urllib2.HTTPError):
      # cloning can be very long.
      # XXX: quite dirty way to check.
      while self._connectToSlaprunner('getProjectStatus', data='project=workspace/slapos').find('On branch master') is -1:
        self.logger.info('git-cloning ongoing, sleeping...')

    # XXX should be taken from parameter.
    self._connectToSlaprunner(resource='setCurrentProject', data='path=workspace/slapos/software/helloworld/')

    self.logger.info('Building the Software Release...')
    try:
      self._connectToSlaprunner(resource='runSoftwareProfile')
    except (NotHttpOkException, urllib2.HTTPError):
      # The nginx frontend might timeout before software release is finished.
      pass
    while self._connectToSlaprunner(resource='slapgridResult', data='position=0&log=').find('"software": true') is not -1:
      self.logger.info('Buildout is still running. Sleeping...')
      time.sleep(15)
    self.logger.info('Software Release has been built.')

    self.logger.info('Deploying instance...')
    try:
      self._connectToSlaprunner(resource='runInstanceProfile')
    except (NotHttpOkException, urllib2.HTTPError):
      # The nginx frontend might timeout before someftware release is finished.
      pass
    while self._connectToSlaprunner(resource='slapgridResult', data='position=0&log=').find('"instance": true') is not -1:
      self.logger.info('Buildout is still running. Sleeping...')
      time.sleep(15)
    self.logger.info('Instance has been deployed.')

    self.data = self._retrieveInstanceLogFile()


  def checkDataOnCloneInstance(self):
    """
    Check that:
      * backend_url is different
      * Software Release profile is the same,
      * Software Release is built and is the same, (?)
      * Instance is deployed and is the same.
    """
    # XXX: does the promise wait for the software to be built and the instance to be ready?
    old_slaprunner_backend_url = self.slaprunner_backend_url
    self.slaprunner_backend_url = self._returnNewInstanceParameter(
        parameter_key='backend_url',
        old_parameter_value=old_slaprunner_backend_url
    )
    self._login()
    new_data = self._retrieveInstanceLogFile()

    if new_data == self.data:
      self.logger.info('Data are the same: success.')
      return True
    else:
      self.logger.info('Data are different: failure.')


def runTestSuite(*args, **kwargs):
  """
  Run Slaprunner Resiliency Test.
  """
  return SlaprunnerTestSuite(*args, **kwargs).runTestSuite()
