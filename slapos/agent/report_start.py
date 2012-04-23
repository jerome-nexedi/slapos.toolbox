import ConfigParser, argparse, pprint, socket, sys, time, xmlrpclib, json

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
  if master_url[-1] != '/':
    master_url += '/'
  master = xmlrpclib.ServerProxy("%s%s" %
            (master_url, 'portal_task_distribution'),
            allow_none=1)
  assert master.getProtocolRevision() == 1
  software_list = json.loads(configuration.get("agent", "software_list"))
  test_result = safeRpcCall(master.createTestResult,
    "SlapOS Test", "", software_list,
    True, "SlapOS Test", "SlapOS Test Agent", "ViFiB Project")
  test_result_path, revision = test_result
  state = ConfigParser.SafeConfigParser()
  state.add_section("path")
  exclude_list = software_list[:]
  for software in software_list:
    exclude_list.remove(software)
    test_path, test_name = safeRpcCall(master.startUnitTest,
      test_result_path, exclude_list)
    state.set("path", test_name, test_path)
    exclude_list.append(software)
  path_file = configuration.get("agent", "path_file")
  state.write(open(path_file, "w"))

if __name__ == "__main__":
  main()
