# -*- coding: utf-8 -*-
# vim: set et sts=2:
# pylint: disable-msg=W0311,C0301,C0103,C0111,R0904,R0903

import ConfigParser
import datetime
import logging
import logging.handlers
from optparse import OptionParser, Option
import os
from slapos.runner.process import setHandler
import sys
from slapos.runner.utils import (runInstanceWithLock,
                                 cloneDefaultGit, setupDefaultSR)
from slapos.runner.views import *


class Config:
  def __init__(self):
    self.configuration_file_path = None
    self.console = None
    self.log_file = None
    self.logger = None
    self.verbose = None

  def setConfig(self):
    """
    Set options given by parameters.
    """
    self.configuration_file_path = os.path.abspath(os.getenv('RUNNER_CONFIG'))

    # Load configuration file
    configuration_parser = ConfigParser.SafeConfigParser()
    configuration_parser.read(self.configuration_file_path)

    for section in ("slaprunner", "slapos", "slapproxy", "slapformat",
                    "sshkeys_authority", "gitclient", "cloud9_IDE"):
      configuration_dict = dict(configuration_parser.items(section))
      for key in configuration_dict:
        if not getattr(self, key, None):
          setattr(self, key, configuration_dict[key])

    # set up logging
    self.logger = logging.getLogger("slaprunner")
    self.logger.setLevel(logging.INFO)
    if self.console:
      self.logger.addHandler(logging.StreamHandler())

    self.log_file = self.log_dir + '/slaprunner.log'
    if not os.path.isdir(os.path.dirname(self.log_file)):
    # fallback to console only if directory for logs does not exists and
    # continue to run
      raise ValueError('Please create directory %r to store %r log file' % (
      os.path.dirname(self.log_file), self.log_file))
    else:
      file_handler = logging.FileHandler(self.log_file)
      file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
      self.logger.addHandler(file_handler)
      self.logger.info('Configured logging to file %r' % self.log_file)

    self.logger.info("Started.")
    self.logger.info(os.environ['PATH'])
    if self.verbose:
      self.logger.setLevel(logging.DEBUG)
      self.logger.debug("Verbose mode enabled.")


def run():
  "Run default configuration."
  usage = "usage: %s [options] CONFIGURATION_FILE" % sys.argv[0]

  try:
    # Parse arguments
    config = Config()
    config.setConfig()

    if os.getuid() == 0:
      # avoid mistakes (mainly in development mode)
      raise Exception('Do not run SlapRunner as root.')

    serve(config)
    return_code = 0
  except:
    e = sys.exc_info()[0]
    sys.exit(e)

def serve(config):
  from werkzeug.contrib.fixers import ProxyFix
  workdir = os.path.join(config.runner_workdir, 'project')
  software_link = os.path.join(config.runner_workdir, 'softwareLink')
  app.config.update(**config.__dict__)
  app.config.update(
    software_log=config.software_root.rstrip('/') + '.log',
    instance_log=config.instance_root.rstrip('/') + '.log',
    workspace=workdir,
    software_link=software_link,
    instance_profile='instance.cfg',
    software_profile='software.cfg',
    SECRET_KEY=os.urandom(24),
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=31),
  )
  if not os.path.exists(workdir):
    os.mkdir(workdir)
  if not os.path.exists(software_link):
    os.mkdir(software_link)
  setHandler()
  config.logger.info('Running slapgrid...')
  runInstanceWithLock(app.config)
  config.logger.info('Done.')
  app.wsgi_app = ProxyFix(app.wsgi_app)

run()
