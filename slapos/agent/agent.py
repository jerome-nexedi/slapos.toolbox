from random import random, choice
import os
import socket
import time
from datetime import datetime
from datetime import timedelta
import xmlrpclib
from logging import getLogger, basicConfig

MAXIMUM_SOFTWARE_INSTALLATION_DURATION = timedelta(minutes = 120)
MAXIMUM_SOFTWARE_CLEANUP_DURATION = timedelta(minutes = 15)
SOFTWARE_RELEASE_DESTROYING_RATIO = 0.01
MAXIMUM_SOFTWARE_INSTALLATION_COUNT = 5

def safeRpcCall(proxy, function_id, *args):
  try:
    function = getattr(proxy, function_id)
    return function(*args)
  except (socket.error, xmlrpclib.ProtocolError, xmlrpclib.Fault), e:
    pass

class Agent:
  def __init__(self):
    self.computer_list = []
    self.software_release_list = []
    self.portal_url = ""
    basicConfig(format="%(asctime)-15s %(message)s", level="INFO")
    self.logger = getLogger()

  def getDestroyingSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getDestroyingSoftwareReleaseReferenceListOnComputer", computer, self.software_release_list)

  def getInstalledSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getInstalledSoftwareReleaseReferenceListOnComputer", computer, self.software_release_list)

  def getInstallingSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getInstallingSoftwareReleaseReferenceListOnComputer", computer, self.software_release_list)

  def getSoftwareReleaseCleanupStartDateOnComputer(self, computer, software_release):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    start_date_string = safeRpcCall(portal, "Agent_getSoftwareReleaseCleanupStartDateOnComputer", computer, software_release)
    if start_date_string is not None:
      return datetime.strptime(start_date_string, "%Y-%m-%dT%H:%M:%S")
    return None

  def getSoftwareReleaseSetupStartDateOnComputer(self, computer, software_release):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    start_date_string = safeRpcCall(portal, "Agent_getSoftwareReleaseSetupStartDateOnComputer", computer, software_release)
    if start_date_string is not None:
      return datetime.strptime(start_date_string, "%Y-%m-%dT%H:%M:%S")
    return None

  def getSoftwareReleaseUsageOnComputer(self, computer, software_release):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getSoftwareReleaseUsageOnComputer", computer, software_release)

  def requestSoftwareReleaseCleanupOnComputer(self, computer, software_release):
    self.logger.info("Request to cleanup %s on %s." % (software_release, computer))
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    safeRpcCall(portal, "Agent_requestSoftwareReleaseCleanupOnComputer", computer, software_release)
    time.sleep(5)

  def requestSoftwareReleaseInstallationOnComputer(self, computer, software_release):
    self.logger.info("Request to install %s on %s." % (software_release, computer))
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    safeRpcCall(portal, "Agent_requestSoftwareReleaseInstallationOnComputer", computer, software_release)
    time.sleep(5)

  def stopSoftwareReleaseCleanupOnComputer(self, computer, software_release):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    safeRpcCall(portal, "Agent_stopSoftwareReleaseCleanupOnComputer", computer, software_release)
    time.sleep(5)

  def stopSoftwareReleaseInstallationOnComputer(self, computer, software_release):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    safeRpcCall(portal, "Agent_stopSoftareReleaseInstallationOnComputer", computer, software_release)
    time.sleep(5)

  def checkSoftwareReleaseStatus(self):
    now = datetime.now()
    for computer in self.computer_list:
      installing_software_release_list = self.getInstallingSoftwareReleaseListOnComputer(computer)
      for software_release in installing_software_release_list:
        start_date = self.getSoftwareReleaseSetupStartDateOnComputer(computer, software_release)
        if start_date is not None:
          duration = now - start_date
          if duration > MAXIMUM_SOFTWARE_INSTALLATION_DURATION:
            self.logger.error("Failed to install %s on %s in %s." % (software_release, computer, duration))
          if duration > 2 * MAXIMUM_SOFTWARE_INSTALLATION_DURATION:
            self.requestSoftwareReleaseCleanupOnComputer(computer, software_release)
    for computer in self.computer_list:
      destroying_software_release_list = self.getDestroyingSoftwareReleaseListOnComputer(computer)
      for software_release in destroying_software_release_list:
        start_date = self.getSoftwareReleaseCleanupStartDateOnComputer(computer, software_release)
        if start_date is not None:
          duration = now - start_date
          if duration > MAXIMUM_SOFTWARE_CLEANUP_DURATION:
            self.logger.error("Failed to cleanup %s on %s in %s." % (software_release, computer, duration))

  def do(self):
    for computer in self.computer_list:
      installing_software_release_list = self.getInstallingSoftwareReleaseListOnComputer(computer)
      installed_software_release_list = self.getInstalledSoftwareReleaseListOnComputer(computer)
      if len(installing_software_release_list) < MAXIMUM_SOFTWARE_INSTALLATION_COUNT:
        software_release = choice(self.software_release_list)
        if not software_release in installing_software_release_list + installed_software_release_list:
          self.requestSoftwareReleaseInstallationOnComputer(computer, software_release)
    now = datetime.now()
    for computer in self.computer_list:
      installed_software_release_list = self.getInstalledSoftwareReleaseListOnComputer(computer)
      for software_release in installed_software_release_list:
        if self.getSoftwareReleaseUsageOnComputer(computer, software_release) == 0:
          if random() < SOFTWARE_RELEASE_DESTROYING_RATIO:
            self.requestSoftwareReleaseCleanupOnComputer(computer, software_release)

if __name__ == "__main__":
  agent = Agent()
  agent.checkSoftwareReleaseStatus()
  agent.do()
