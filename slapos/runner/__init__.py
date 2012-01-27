from optparse import OptionParser, Option
import ConfigParser
import logging
import logging.handlers
import os
import sys
import subprocess

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
      Option("-l", "--log_file",
             help="The path to the log file used by the script.",
             type=str),
      Option("-v", "--verbose",
             default=False,
             action="store_true",
             help="Verbose output."),
      Option("-c", "--console",
             default=False,
             action="store_true",
             help="Console output."),
      Option("-d", "--debug",
             default=False,
             action="store_true",
             help="Debug mode."),
    ])

  def check_args(self):
    """
    Check arguments
    """
    (options, args) = self.parse_args()
    if len(args) != 1:
      self.error("Incorrect number of arguments")

    return options, args[0]

class Config:
  def setConfig(self, option_dict, configuration_file_path):
    """
    Set options given by parameters.
    """
    self.configuration_file_path = os.path.abspath(configuration_file_path)
    # Set options parameters
    for option, value in option_dict.__dict__.items():
      setattr(self, option, value)

    # Load configuration file
    configuration_parser = ConfigParser.SafeConfigParser()
    configuration_parser.read(configuration_file_path)
    # Merges the arguments and configuration
    
    for section in ("slaprunner", "slapos", "slapproxy", "slapformat", "sshkeys_authority", "gitclient"):
      configuration_dict = dict(configuration_parser.items(section))
      for key in configuration_dict:
        if not getattr(self, key, None):
          setattr(self, key, configuration_dict[key])

    # set up logging
    self.logger = logging.getLogger("slaprunner")
    self.logger.setLevel(logging.INFO)
    if self.console:
      self.logger.addHandler(logging.StreamHandler())

    if self.log_file:
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
    config.setConfig(*Parser(usage=usage).check_args())

    serve(config)
    return_code = 0
  except SystemExit, err:
    # Catch exception raise by optparse
    return_code = err

  sys.exit(return_code)

def serve(config):
  from views import app
  workdir = os.path.join(config.runner_workdir, 'project')
  app.config.update(**config.__dict__)
  app.config.update(
    software_log=config.software_root.rstrip('/') + '.log',
    instance_log=config.instance_root.rstrip('/') + '.log',
    workspace = workdir,
    instance_profile='instance.cfg',
    software_profile='software.cfg',
    SECRET_KEY='123',
  )
  if not os.path.exists(workdir):
    os.mkdir(workdir)
  app.run(host=config.runner_host, port=int(config.runner_port),
      debug=config.debug, threaded=True)
