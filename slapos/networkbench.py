import socket
import logging
import time
import ConfigParser
import logging.handlers
import urllib2
import subprocess
import re
import sys
import shutil
import netifaces
import random

botname = socket.gethostname()

# rtt min/avg/max/mdev = 1.102/1.493/2.203/0.438 ms
ping_re = re.compile(
    ".*"
    "(?P<min>[\d\.]+)/"
    "(?P<max>[\d\.]+)/"
    "(?P<avg>[\d\.]+)/"
    "(?P<mdev>[\d\.]+) ms"
    )

date_reg_exp = re.compile('\d{4}[-/]\d{2}[-/]\d{2}')

def _get_network_gateway(self):
  return netifaces.gateways()["default"][netifaces.AF_INET][0]

def _test_dns(name):
  begin = time.time()
  try:
    socket.gethostbyname(name)
    resolution = 200
    status = "OK"
  except socket.gaierror:
    resolution = 600
    status = "Cannot resolve the hostname"

  resolving_time = time.time() - begin
  return ('DNS', name, resolution, resolving_time, status)

def _test_ping(host, timeout=10):
  proc = subprocess.Popen(('ping', '-c', '4', '-w', str(timeout), host), 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  out, err = proc.communicate()
  packet_loss_line, summary_line = (out.splitlines() or [''])[-2:]
  m = ping_re.match(summary_line)
  info_list = ('PING', host, '600', 'failed', "Cannot ping host")
  if ' 0% packet loss' in packet_loss_line:
    if m:
      info_list = ('PING', host, '200', m.group('avg'),
           'min %(min)s max %(max)s avg %(avg)s' % m.groupdict())

  return info_list

def _test_url_request(url, request):
  begin = time.time()
  try:
    response = urllib2.urlopen(request)
    if url != response.url:
      raise RuntimeError, 'Redirected to %s' % response.url
    response.read()
    rendering_time = time.time() - begin
    info_list = ('GET', url, response.code, rendering_time, "OK")
  except urllib2.HTTPError, e: # 40x errors
    e.fp.read()
    rendering_time = time.time() - begin
    info_list = ('GET', url, e.code, rendering_time, "HTTPError")
  except urllib2.URLError, e: # DNS failure
    rendering_time = time.time() - begin
    info_list = ('GET', url, '600', rendering_time, "DNS Failure")
  except RuntimeError, e:
    info_list = ('GET', url, '600', 'failed')

  return info_list

def is_rotate_log(log_file_path):
  try:
    log_file = open(log_file_path, 'r')
  except IOError:
    return False

  # Handling try-except-finally together.
  try:
    try:
      log_file.seek(0, 2)
      size = log_file.tell()
      log_file.seek(-min(size, 4096), 1)
      today = time.strftime("%Y-%m-%d")
      
      for line in reversed(log_file.read().split('\n')):
        if len(line.strip()):
          match_list = date_reg_exp.findall(line)
          if len(match_list):
            if match_list[0] != today:
              return ValueError(match_list[0])
            break

    except IOError:
      return False
  finally:
    log_file.close()

def create_logger(name, log_folder):
  new_logger = logging.getLogger(name)

  new_logger.setLevel(logging.DEBUG)
  log_file = '%s/network_bench.%s.log' % (log_folder, name)
  handler = logging.handlers.TimedRotatingFileHandler(
                     log_file, when="D",
                     backupCount=1000)

  last_date = is_rotate_log(log_file)
  if last_date:
    handler.doRollover()
    today = time.strftime("%Y-%m-%d")
    shutil.move("%s.%s" % (log_file, today),
                "%s.%s" % (log_file, last_date))
    # The simpler the better
    sp = subprocess.Popen("gzip %s.%s" % (log_file, last_date),
               stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    sp.communicate()

  format = "%%(asctime)-16s;%%(levelname)s;%s;%%(message)s" % botname
  handler.setFormatter(logging.Formatter(format))
  new_logger.addHandler(handler)
  return new_logger

def main():
  if len(sys.argv) not in [2, 3]:
    print " USAGE: %s configuration_file [log_folder]" % sys.argv[0]
    return

  config = ConfigParser.ConfigParser()
  config.read(sys.argv[1])

  if len(sys.argv) == 3:
    log_folder = sys.argv[2]
  else:
    log_folder = "."

  delay = random.randint(0, 30)

  name_list = config.get("network_bench", "dns")
  url_list = config.get("network_bench", "url")
  ping_list = config.get("network_bench", "ping")

  logger = create_logger("info", log_folder)

  logger.debug('Starting a new test in %s seconds' % delay)

  time.sleep(delay)

  for name in name_list.split():
    info_list = _test_dns(name)
    logger.info(';'.join(str(x) for x in info_list))

  # ping
  for host in ping_list.split():
    info_list = _test_ping(host)
    logger.info(';'.join(str(x) for x in info_list))

  # http
  for url in url_list.split():
    info_list = _test_url_request(url, urllib2.Request(url))
    logger.info(';'.join(str(x) for x in info_list))

