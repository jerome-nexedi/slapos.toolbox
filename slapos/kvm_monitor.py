# -*- coding: utf-8 -*-

from ConfigParser import RawConfigParser
from lxml.etree import Element, SubElement, ElementTree
from argparse import ArgumentParser

class MonitorConfig():
  """
  Class used for parsing the configuration file
  and returning a dict with the selected options and their values
  """

  def __init__(self,filepath,sections,options):
    """
    filepath : path to configuration file that need to be parsed
    sections : sections in which the options we need can be found
    options : options that we need to check for billing
    """
    self.filepath = filepath
    self.sections = sections
    self.options = options
    self.parser = RawConfigParser()
    self.parser.optionxform = lambda s: s

  def getConfig(self):
    """
    Method for parsing the configuration file and
    returning the dict of options
    """
    result = {}
    conf_file = open(self.filepath)
    self.parser.readfp(conf_file)
    
    for section in self.sections:
      tmp_dict = dict(self.parser.items(section))
      for option in self.options:
        result[option] = tmp_dict.get(option,"")
      
    conf_file.close()
    return result

class GenerateXMLFile():
  """
  Class used to serialize the dict of options and output it to XML
  """
  
  def __init__(self,xml_filepath,conso_dict):
    """
    xml_filepath : path to the XML output file
    conso_dict : dict of options 
    (generated by the previous class method getConfig)
    """
    self.xml_filepath = xml_filepath
    self.element_tree = self._serializeDictToElementTree(conso_dict)

  def _serializeDictToElementTree(self,info_dict):
    """
    Transform the dict of options into XML
    return ElementTree
    """
    result = ElementTree(Element("data"))
    root = result.getroot()
    for key, value in info_dict.items():
      tmp = SubElement(root,key)
      tmp.text = value

    return result

  def outputFile(self):
    """
    Write the XML to a file
    """
    self.element_tree.write(self.xml_filepath,encoding="utf-8",xml_declaration=True)
    
def parseCli():
  """
  Parser definition for the command line interface
  """
  usage = """ %(prog)s <filepath> <xml-path> -s [sections] -opts [options] """
  parser = ArgumentParser(prog="kvm_monitor.py", usage=usage)

  parser.add_argument("filepath",
                      help="Path to the configuration file with the informations"
  )
  
  parser.add_argument("xml_path",
                      help="Path to the xml output file"
  )

  parser.add_argument("-s","--sections", nargs='+', required=True,
                      help="Sections in which the informations can be found." +
                      "Each section should be separated by a space."
  )

  parser.add_argument("-opts","--options", nargs='+', required=True,
                      help="Options that need to be reported by the monitor." +
                      "Each option should be separated by a space."
  )

  return parser

def runMonitor():
  """
  Procedure called to run the monitoring (from parsing the configuration file
  to the XML output)
  """
  parser = parseCli()
  args = parser.parse_args()

  info_dict = MonitorConfig(args.filepath,
            args.sections,
            args.options
  ).getConfig()

  serializer = GenerateXMLFile(args.xml_path,info_dict)
  serializer.outputFile()
