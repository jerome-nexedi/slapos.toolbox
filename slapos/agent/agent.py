import ConfigParser, argparse
import json
from random import choice
import os, socket, time
from datetime import datetime
from datetime import timedelta
import xmlrpclib
from logging import getLogger, basicConfig
from slapos.slap import slap, Supply
from slapos.grid.utils import setRunning, setFinished

def safeRpcCall(proxy, function_id, *args):
  while True:
    try:
      function = getattr(proxy, function_id)
      return function(*args)
    except (socket.error, xmlrpclib.ProtocolError, xmlrpclib.Fault), e:
      time.sleep(64)

def _encode_software_dict(software_dict):
  result = dict()
  for key, value in software_dict.items():
    result[key] = datetime.strftime(value, "%Y-%m-%dT%H:%M:%S")
  return result

def _decode_software_dict(software_dict):
  result = dict()
  for key, value in software_dict.items():
    result[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
  return result

class Agent:
  def __init__(self, portal_url, master_url,
        maximum_software_installation_duration, software_live_duration,
        computer_list, software_list, log_directory, state_file, software_uri,
        key_file=None, cert_file=None,
      ):
    self.portal_url = portal_url
    master_url = master_url
    key_file = key_file
    cert_file = cert_file
    self.maximum_software_installation_duration = \
      maximum_software_installation_duration
    self.software_live_duration = software_live_duration
    self.computer_list = computer_list
    self.software_list = software_list
    self.software_uri = software_uri
    self.log_directory = log_directory
    self.state_file = state_file

    filename = os.path.join(self.log_directory, "agent-%s.log" % datetime.strftime(datetime.now(), "%Y%m%d"))
    basicConfig(filename=filename, format="%(asctime)-15s %(message)s", level="INFO")
    self.logger = getLogger()

    self.slap = slap()
    self.slap.initializeConnection(master_url, key_file, cert_file)
    self.supply = Supply()

    state = ConfigParser.SafeConfigParser()
    state.readfp(open(self.state_file))
    self.installing_software_dict = dict()
    self.installed_software_dict = dict()
    for computer in self.computer_list:
      if state.has_section(computer):
        self.installing_software_dict[computer] = \
            _decode_software_dict(json.loads(state.get(computer, "installing_software", "{}")))
        self.installed_software_dict[computer] = \
            _decode_software_dict(json.loads(state.get(computer, "installed_software", "{}")))
      else:
        self.installing_software_dict[computer] = dict()
        self.installed_software_dict[computer] = dict()

  def getDestroyingSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getDestroyingSoftwareReleaseReferenceListOnComputer", computer, self.software_list)

  def getInstalledSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getInstalledSoftwareReleaseReferenceListOnComputer", computer, self.software_list)

  def getInstallingSoftwareReleaseListOnComputer(self, computer):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getInstallingSoftwareReleaseReferenceListOnComputer", computer, self.software_list)

  def getSoftwareReleaseUsageOnComputer(self, computer, software):
    portal = xmlrpclib.ServerProxy(self.portal_url, allow_none=1)
    return safeRpcCall(portal, "Agent_getSoftwareReleaseUsageOnComputer", computer, software)

  def requestSoftwareReleaseCleanupOnComputer(self, computer, software):
    try:
      self.supply.supply(self.software_uri[software], computer, "destroyed")
      self.logger.info("Successfully requested to cleanup %s on %s." % (software, computer))
      return True
    except:
      self.logger.info("Failed to request to cleanup %s on %s." % (software, computer))
      return False

  def requestSoftwareReleaseInstallationOnComputer(self, computer, software):
    try:
      self.supply.supply(self.software_uri[software], computer, "available")
      self.logger.info("Successfully requested to install %s on %s." % (software, computer))
      return True
    except:
      self.logger.info("Failed to request to install %s on %s." % (software, computer))
      return False

  def writeState(self):
    state = ConfigParser.SafeConfigParser()
    for computer in self.computer_list:
      state.add_section(computer)
      state.set(computer, "installing_software", \
          json.dumps(_encode_software_dict(self.installing_software_dict[computer])))
      state.set(computer, "installed_software", \
          json.dumps(_encode_software_dict(self.installed_software_dict[computer])))
    state.write(open(self.state_file, "w"))

def main(*args):
  parser = argparse.ArgumentParser()
  parser.add_argument("--pidfile", help="The location where pidfile will be created.")
  parser.add_argument("configuration_file", nargs=1, type=argparse.FileType(),
      help="Slap Test Agent configuration file.")
  if args:
    argument_option_instance = parser.parse_args(list(args))
  else:
    argument_option_instance = parser.parse_args()
  configuration = ConfigParser.SafeConfigParser()
  configuration.readfp(argument_option_instance.pop("configuration_file")[0])
  configuration_dict = dict(configuration.items("agent"))
  configuration_dict.update(argument_option_instance.__dict__)
  pidfile = option_dict.get("pidfile")
  if pidfile:
    setRunning(pidfile)
  agent = Agent(
    portal_url=configuration_dict["portal_url"],
    master_url=configuration_dict["master_url"],
    maximum_software_installation_duration=timedelta(minutes=float(
      configuration_dict["maximum_software_installation_duration"])),
    software_live_duration=timedelta(minutes=float(configuration_dict[
      "software_live_duration"])),
    computer_list=json.loads(configuration_dict["computer_list"]),
    software_list=json.loads(configuration_dict["software_list"]),
    log_directory=configuration_dict["log_directory"],
    state_file=configuration_dict["state_file"],
    software_uri=dict(configuration.items("software_uri")),
    key_file=configuration_dict.get("key_file", None),
    cert_file=configuration_dict.get("cert_file", None),
  )
  now = datetime.now()
  for computer in agent.computer_list:
    installing_software_list = agent.getInstallingSoftwareReleaseListOnComputer(computer)
    installed_software_list = agent.getInstalledSoftwareReleaseListOnComputer(computer)
    destroying_software_list = agent.getDestroyingSoftwareReleaseListOnComputer(computer)
    if len(installing_software_list) == 0:
      software = choice(agent.software_list)
      if software in installed_software_list or software in destroying_software_list:
        pass
      else:
        if agent.requestSoftwareReleaseInstallationOnComputer(computer, software):
          agent.installing_software_dict[computer][software] = datetime.now()
    else:
      for installing_software in installing_software_list:
        if installing_software in agent.installing_software_dict[computer]:
          start_time = agent.installing_software_dict[computer][installing_software]
          if now - start_time > agent.maximum_software_installation_duration:
            agent.logger.info("Failed to install %s on %s in %s." % \
                (installing_software, computer, agent.maximum_software_installation_duration))
            if agent.requestSoftwareReleaseCleanupOnComputer(computer, installing_software):
              del agent.installing_software_dict[computer][installing_software]
    for installed_software in installed_software_list:
      if installed_software in agent.installing_software_dict[computer]:
        agent.logger.info("Successfully installed %s on %s." % (installed_software, computer))
        del agent.installing_software_dict[computer][installed_software]
        agent.installed_software_dict[computer][installed_software] = now
      elif installed_software in agent.installed_software_dict[computer] and \
          agent.getSoftwareReleaseUsageOnComputer(computer, installed_software) == 0 and \
          now - agent.installed_software_dict[computer][installed_software] > agent.software_live_duration:
        if agent.requestSoftwareReleaseCleanupOnComputer(computer, installed_software):
          del agent.installed_software_dict[computer][installed_software]
  agent.writeState()

  if pidfile:
    setFinished(pidfile)

if __name__ == "__main__":
  main()
