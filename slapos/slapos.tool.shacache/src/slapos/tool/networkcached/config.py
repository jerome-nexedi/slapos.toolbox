##############################################################################
#
# Copyright (c) 2010 ViFiB SARL and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################


import os
import logging
import logging.handlers
import ConfigParser
from optparse import OptionParser, Option


class NetworkcacheParser(OptionParser):
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
      Option("-d", "--cache_base_folder",
             type=str,
             help="Folder to store the files."),
      Option("-a", "--host",
             type=str,
             help="Host address."),
      Option("-p", "--port",
             type=str,
             help="Port number."),
    ])

  def check_args(self):
    """
      Check arguments
    """
    (options, args) = self.parse_args()
    configuration_file_path = []

    if len(args) > 1:
      self.error("Incorrect number of arguments")

    if len(args) == 1:
      configuration_file_path = args[0]

    return options, configuration_file_path


class NetworkcacheConfiguration:
  def setConfig(self, option_dict, configuration_file_path):
    """
    Set options given by parameters.
    """
    # Set options parameters
    for option, value in option_dict.__dict__.items():
      setattr(self, option, value)

    # Load configuration file
    if configuration_file_path:
      configuration_parser = ConfigParser.SafeConfigParser()
      configuration_parser.read(configuration_file_path)
      # Merges the arguments and configuration
      for section in ("networkcached",):
        configuration_dict = dict(configuration_parser.items(section))
        for key in configuration_dict:
          if not getattr(self, key, None):
            setattr(self, key, configuration_dict[key])

    # set up logging
    self.logger = logging.getLogger("networkcached")
    self.logger.setLevel(logging.INFO)
    if self.console:
      self.logger.addHandler(logging.StreamHandler())

    # cache base folder is required
    if not self.cache_base_folder:
      raise ValueError('cache_base_folder is required.')

    if self.log_file:
      if not os.path.isdir(os.path.dirname(self.log_file)):
        # fallback to console only if directory for logs does not exists and
        # continue to run
        raise ValueError('Please create directory %r to store %r log file' % (
          os.path.dirname(self.log_file), self.log_file))
      else:
        file_handler = logging.FileHandler(self.log_file)
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(format))
        self.logger.addHandler(file_handler)
        self.logger.info('Configured logging to file %r' % self.log_file)

    self.logger.info("Started.")
    if self.verbose:
      self.logger.setLevel(logging.DEBUG)
      self.logger.debug("Verbose mode enabled.")
