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
import datetime
import os
import time
import resource
from time import strftime
import logging
import sys
from lxml import etree as ElementTree
import platform
import psutil
from optparse import OptionParser
import tempfile
import sqlite3.dbapi2 as sqlite3

#define global variable for log file
log_file = False

class MonitoringTool(object):
  """Provide functions to monitor CPU and Memory"""
  def __init__(self):
    pass

  def get_cpu_and_memory_usage(self, proc):
    """Return CPU and Memory usage (percent) and 
    the specific moment used for the measure"""
    return [proc.get_cpu_percent(), sum(proc.get_cpu_times()), proc.get_memory_percent(), proc.get_memory_info()[0], datetime.datetime.now()]

class GenerateXML(object):
  """Return a XML file upon request by reading from database"""
  
  def __init__(self, element_tree, path_database, path_xml):
    self.element_tree = element_tree
    self.path_database = path_database
    self.path_xml = path_xml

  def dump_xml(self):
    """This func read data from database and through
    _write_xml_output write result on xml file"""  

    consumption_infos = []
    #This list hold the consuption infos in the following order
    #[CPU % usage, CPU time usage (seconds), Memory % usage, Memory space usage (byte), date, time]
    
    conn = sqlite3.connect(self.path_database)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM data")
    for row in cursor:
      consumption_infos.append(row)

    #If the database is not empty
    if consumption_infos != []:
      consumption_summary = self._eval_consumption_summary (consumption_infos)
      self._write_xml_output(consumption_summary, self.path_xml)

    #Once we got infos we delete the table 'data'
    cursor.execute("DELETE FROM data")
    conn.commit()
    cursor.close()
    conn.close()

  def _eval_consumption_summary(self, consumption_infos):
    """This function return a resources usage summary, for pricing purpose"""
    memory_percentage = []
    memory_space = []
    cpu_time = []
    total_cpu_time = 0.00
    previous = 0.00
    first_time = False
    
    #The total time that the cpu spent to work on it
    #Start-end time and date
    start_time = consumption_infos[0][5]
    end_time = consumption_infos[-1][5]
    start_date = consumption_infos[0][4]
    end_date = consumption_infos[-1][4]
    
    for item in consumption_infos:
      cpu_time.append(item[1])
      memory_percentage.append(item[2])
      memory_space.append(item[3])
  
    #For all the samples, we calculate CPU consumption time
    for indice,element in enumerate(cpu_time):
      if indice == 0:
        first_sample = float(element)
        first_time = True
      else:
        #If the partition has been restarted...
        if previous > float(element):
          #If the partition has been restarted for the first time...
          if first_time:
            #We count the usage before the stop
            previous = previous - first_sample
            first_time = False
          total_cpu_time = total_cpu_time + previous
        previous = float(element)
    #If the partition hasn't been restarted, we count only the difference between the last and the first sample
    if first_time:
      total_cpu_time = cpu_time[-1] - first_sample
    #Else, we add the last sample to the total CPU consumption time
    else:
      total_cpu_time = total_cpu_time + cpu_time[-1] 
    
    return [total_cpu_time, sum(memory_space) / float(len(memory_space)), start_time, end_time, start_date, end_date]
    #return [scipy.mean(cpu_percentage), cpu_time, scipy.mean(memory_percentage),
    #      scipy.mean(memory_space), start_time, end_time, start_date, end_date]



  def _write_xml_output(self, res_list, storage_path):
    """This function provide to dump on xml the consumption infos, 
    the res_list contains the following informations:

    [CPU mean %, CPU whole usage (seconds), Memory mean %, Memory mean space usage (byte), 
    start_time, end_time, start_date, end_date]"""

    #XXX- NOTE

    """The res_list has been recently changed, now it contains  
    [CPU whole usage (seconds), Memory mean space usage (byte)]"""
    

    res_list = map(str, res_list)

    cpu_list = ['CPU Consumption',
                'CPU consumption of the partition on %s at %s' % (res_list[5], res_list[3]),
                res_list[0], 
                ]

    memory_list = ['Memory consumption', 
                  'Memory consumption of the partition on %s at %s' % (res_list[5], res_list[3]),
                  res_list[1],
                  ]

    root = ElementTree.Element("consumption")
    #Then, we add two movement elements, one for cpu
    tree = self._add_movement(root, cpu_list )
    #And one for memory
    tree = self._add_movement(root, memory_list)

    #We add the XML header to the file to be valid
    report = ElementTree.tostring(tree)
    fd = open(storage_path, 'w')
    fd.write("<?xml version='1.0' encoding='utf-8'?>%s" % report)
    fd.close() 
  
  def _add_movement(self, consumption, single_resource_list):
    
    child_consumption = ElementTree.SubElement(consumption, "movement")

    child_movement = ElementTree.SubElement(child_consumption, "resource")
    child_movement.text = single_resource_list[0]
    child_movement = ElementTree.SubElement(child_consumption, "title")
    child_movement.text = single_resource_list[1]
    child_movement = ElementTree.SubElement(child_consumption, "reference")
    child_movement.text = ''
    child_movement = ElementTree.SubElement(child_consumption, "quantity")
    child_movement.text = single_resource_list[2]
    child_movement = ElementTree.SubElement(child_consumption, "price")
    child_movement.text = '0.00'
    child_movement = ElementTree.SubElement(child_consumption, "VAT")
    child_movement.text = ''
    child_movement = ElementTree.SubElement(child_consumption, "category")
    child_movement.text = ''

    tree = self.element_tree.ElementTree(consumption)
    return tree


def parse_opt():

  usage="""usage: slapmonitor [options] PID_FILE_PATH DATABASE_PATH
Usage: slapreport [options] XML_PATH DATABASE_PATH """

  parser = OptionParser(usage=usage)
  parser.add_option('-t', '--update_time',type=int, dest='update_time', help='Specify the interval'\
                    '(in seconds) to check resources consumption [default 30 seconds]', default=3)
  parser.add_option('-l', '--log_file', dest='path_log_file',help='Specify the logfile destination path',
                    metavar='FILE')
  return parser

class SlapMonitor(object):
    
  def __init__(self, proc, update_time, path_database):
    self.proc = proc
    self.update_time = update_time
    self.path_database = path_database
    self.start_monitor()        
        

  def start_monitor(self):
        
    temporary_monitoring = MonitoringTool()
    #check if the process is alive == None, instead zero value == proc is over
    while self.proc.pid in psutil.get_pid_list():
      conn = sqlite3.connect(self.path_database)
      cursor = conn.cursor()
      cursor.execute("create table if not exists data (cpu real, cpu_time real, memory real, rss real," \
                      "date text, time text)")
      try:
        res_list = temporary_monitoring.get_cpu_and_memory_usage(self.proc)
        date_catched = "-".join([str(res_list[4].year), str(res_list[4].month), str(res_list[4].day)])
        time_catched = ":".join([str(res_list[4].hour), str(res_list[4].minute), str(res_list[4].second)])
        res_list[4] = date_catched
        res_list.append(time_catched)
        cursor.execute("insert into data values (?,?,?,?,?,?)" , res_list)
        conn.commit()
        cursor.close()
        conn.close()
        time.sleep(self.update_time)
      except IOError:
        if log_file: 
          logging.info("ERROR : process with pid : %s watched by slap monitor exited too quickly at %s" 
                % (self.proc.pid, strftime("%Y-%m-%d at %H:%m")))
        sys.exit(1)        
    if log_file:
      logging.info("EXIT 0: Process terminated normally!")
    sys.exit(0)

def run_slapmonitor():
  #This function require the pid file and the database path
  parser = parse_opt()
  opts, args = parser.parse_args()
  if len(args) != 2:
    parser.error("Incorrect number of arguments, 2 required but "+str(len(args))+" detected" )

  if opts.path_log_file:
    logging.basicConfig(filename=opts.path_log_file,level=logging.DEBUG)
    global log_file 
    log_file = True
  
  fed = open(args[0], 'r')
  pid_read = fed.read()
  fed.close()
  proc = psutil.Process(int(pid_read))
  SlapMonitor(proc, opts.update_time, args[1])
  

def run_slapreport():
  #This function require the xml_path and database_path
  parser = parse_opt()
  opts, args = parser.parse_args()
  if len(args) != 2:
    parser.error("Incorrect number of arguments, 2 required but "+str(len(args))+" detected" )

  if opts.path_log_file:
    logging.basicConfig(filename=opts.path_log_file,level=logging.DEBUG)
    global log_file
    log_file = True

  get_xml_hand = GenerateXML(ElementTree, args[1], args[0])
  get_xml_hand.dump_xml()

