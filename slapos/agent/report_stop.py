import ConfigParser, argparse, pprint, socket, sys, time, xmlrpclib, json, os
from datetime import datetime

def safeRpcCall(function, *args):
  retry = 64
  xmlrpc_arg_list = []
  for argument in args:
    if isinstance(argument, dict):
      argument = dict([(x, isinstance(y,str) and xmlrpclib.Binary(y) or y) \
           for (x,y) in argument.iteritems()])
    xmlrpc_arg_list.append(argument)
  while True:
    try:
      return function(*xmlrpc_arg_list)
    except (socket.error, xmlrpclib.ProtocolError), e:
      print >>sys.stderr, e
      pprint.pprint(args, file(function._Method__name, 'w'))
      time.sleep(retry)
      retry += retry >> 1

def main(*args):
  parser = argparse.ArgumentParser()
  parser.add_argument("configuration_file", nargs=1, type=argparse.FileType(),
      help="Slap Test Agent configuration file.")
  if args == ():
    argument_option_instance = parser.parse_args()
  else:
    argument_option_instance = \
      parser.parse_args(list(args))
  configuration_file = argument_option_instance.configuration_file[0]
  configuration = ConfigParser.SafeConfigParser()
  configuration.readfp(configuration_file)
  master_url = configuration.get("agent", "report_url")
  software_list = json.loads(configuration.get("agent", "software_list"))
  if master_url[-1] != '/':
    master_url += '/'
  master = xmlrpclib.ServerProxy("%s%s" %
            (master_url, 'portal_task_distribution'),
            allow_none=1)
  assert master.getProtocolRevision() == 1

  log_directory = configuration.get("agent", "log_directory")
  logfile_path = os.path.join(log_directory, "agent-%s.log" % datetime.strftime(datetime.now(), "%Y%m%d"))
  logfile = open(logfile_path, 'r')
  logline_list = logfile.readlines()

  path_file = configuration.get("agent", "path_file")
  state = ConfigParser.SafeConfigParser()
  state.readfp(open(path_file))
  for software in software_list:
    test_path = state.get("path", software)
    success, failure = 0, 0
    log = ''
    for logline in logline_list:
      success_pattern = "Successfully installed %s" % software
      failure_pattern = "Failed to install %s" % software
      if success_pattern in logline:
        success = success + 1
        log = log + logline
      if failure_pattern in logline:
        failure = failure + 1
        log = log + logline
    safeRpcCall(master.stopUnitTest, test_path,
      {
        "status_code": 0,
        "stderr": log,
        "duration": 0,
        "test_count": success + failure,
        "failure_count": failure
      })

if __name__ == "__main__":
  main()
