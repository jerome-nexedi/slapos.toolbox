import ConfigParser
import argparse
import httplib
import json
import logging
import os
import random
import sys
import tempfile
import traceback
import time
import xmlrpclib
import slapos.slap
from slapos.grid.utils import setRunning, setFinished
from erp5.util.taskdistribution import TaskDistributionTool, RPCRetry

class AutoSTemp(object):
    """
    Create a self-destructing temporary file.
    Uses mkstemp.
    """
    __unlink = os.unlink

    def __init__(self, value):
        fd, self.__name = tempfile.mkstemp()
        os.write(fd, value)
        os.close(fd)

    @property
    def name(self):
        return self.__name

    def __del__(self):
        self.__unlink(self.__name)

# XXX: scripts should be merged in a single one
GET_DESTROYING_METHOD_ID = \
    'Agent_getDestroyingSoftwareReleaseReferenceListOnComputer'
GET_INSTALLED_METHOD_ID = \
    'Agent_getInstalledSoftwareReleaseReferenceListOnComputer'
GET_INSTALLING_METHOD_ID = \
    'Agent_getInstallingSoftwareReleaseReferenceListOnComputer'
SOFTWARE_STATE_UNKNOWN = -1
SOFTWARE_STATE_INSTALLING = 0
SOFTWARE_STATE_INSTALLED = 1
SOFTWARE_STATE_DESTROYING = 2

GET_PARTITION_STATE_METHOD_ID = 'Agent_getComputerPartitionState'
INSTANCE_STATE_UNKNOWN = -1
INSTANCE_STATE_STARTING = 0
INSTANCE_STATE_STARTED = 1
INSTANCE_STATE_STOPPING = 2
INSTANCE_STATE_STOPPED = 3
INSTANCE_STATE_DESTROYING = 4

INSTANCE_STATE_DICT = {
    'Looking for a free partition': INSTANCE_STATE_UNKNOWN,
    'Started': INSTANCE_STATE_STARTED,
    'Start in progress': INSTANCE_STATE_STARTING,
    'Stopped': INSTANCE_STATE_STOPPED,
    'Stop in progress': INSTANCE_STATE_STOPPING,
    'Destruction in progress': INSTANCE_STATE_DESTROYING,
    'Destroyed': INSTANCE_STATE_UNKNOWN,
}

TESTER_STATE_INITIAL = -1
TESTER_STATE_NOTHING = 0
TESTER_STATE_SOFTWARE_INSTALLED = 1
TESTER_STATE_INSTANCE_INSTALLED = 2
TESTER_STATE_INSTANCE_STARTED = 4
TESTER_STATE_INSTANCE_UNISTALLED = 5

class x509Transport(xmlrpclib.Transport):
    """
    Similar to xmlrpclib.SecureTransport, but with actually usable x509
    support.
    """
    def __init__(self, x509, *args, **kw):
        xmlrpclib.Transport.__init__(self, *args, **kw)
        self.__x509 = x509

    def make_connection(self, host):
        if not self._connection or host != self._connection[0]:
            try:
                HTTPSConnection = httplib.HTTPSConnection
            except AttributeError:
                raise NotImplementedError("your version of httplib doesn't "
                    "support HTTPS")
            else:
                chost, self._extra_headers, x509 = self.get_host_info((host,
                    self.__x509))
                self._connection = (host, HTTPSConnection(chost, None, **x509))
        return self._connection[1]

class TestTimeout(Exception):
    pass

class SoftwareReleaseTester(RPCRetry):
    deadline = None
    latest_state = None

    def __init__(self,
                name,
                logger,
                master,
                slap_supply, # slapos supply to manage software release
                slap_order, # slapos open order to manage instance
                url, # software release url
                computer_guid, # computer to use for this test run
                max_install_duration,
                max_uninstall_duration,
                request_kw=None, # instance parameters, if instanciation
                    # testing is desired
                max_request_duration=None,
                max_destroy_duration=None,
            ):
        super(SoftwareReleaseTester, self).__init__(master, 16, logger)
        self.name = name
        self.slap_supply = slap_supply
        self.slap_order = slap_order
        self.url = url
        self.computer_guid = computer_guid
        self.request_kw = request_kw
        self.state = TESTER_STATE_INITIAL
        self.transition_dict = {
            TESTER_STATE_INITIAL: (
                None,
                None,
                TESTER_STATE_NOTHING,
                None,
                None,
            ),
            TESTER_STATE_NOTHING: (
                'install',
                max_install_duration,
                request_kw is None and TESTER_STATE_INSTANCE_UNISTALLED or \
                    TESTER_STATE_SOFTWARE_INSTALLED,
                SOFTWARE_STATE_INSTALLED,
                None,
            ),
            TESTER_STATE_SOFTWARE_INSTALLED: (
                'request',
                max_request_duration,
                TESTER_STATE_INSTANCE_STARTED,
                None,
                INSTANCE_STATE_STARTED,
            ),
            TESTER_STATE_INSTANCE_STARTED: (
                'destroy',
                max_destroy_duration,
                TESTER_STATE_INSTANCE_UNISTALLED,
                None,
                INSTANCE_STATE_UNKNOWN,
            ),
            TESTER_STATE_INSTANCE_UNISTALLED: (
                'uninstall',
                max_uninstall_duration,
                None,
                SOFTWARE_STATE_UNKNOWN,
                None,
            ),
        }

    def __repr__(self):
        deadline = self.deadline
        if deadline is not None:
            deadline -= time.time()
            deadline = '+%is' % (deadline, )
        return '<%s(state=%s, deadline=%s) at %x>' % (
            self.__class__.__name__, self.state, deadline, id(self))

    def _supply(self, state):
        self._logger.info('Supply %s@%s: %s', self.url, self.computer_guid,
            state)
        return self.slap_supply.supply(self.url, self.computer_guid, state)

    def _request(self, state):
        self._logger.info('Request %s@%s: %s', self.url, self.name, state)
        self.latest_state = state
        return self.slap_order.request(
            software_release=self.url,
            partition_reference=self.name,
            state=state,
            **self.request_kw
        )

    def _getSoftwareState(self):
        # TODO: replace with simpler slap-based API
        # TODO: merge all 3 entrypoints into a single, to reduce server load.
        for state, method_id in (
                    (SOFTWARE_STATE_DESTROYING, GET_DESTROYING_METHOD_ID),
                    (SOFTWARE_STATE_INSTALLED, GET_INSTALLED_METHOD_ID),
                    (SOFTWARE_STATE_INSTALLING, GET_INSTALLING_METHOD_ID),
                ):
            if self.url in self._retryRPC(method_id, (self.computer_guid,
                    [self.url])):
                return state
        return SOFTWARE_STATE_UNKNOWN

    def _getInstanceState(self):
        # TODO: replace with simpler slap-based API
        latest_state = self.latest_state
        self._logger.debug('latest_state = %r', latest_state)
        if latest_state is None:
            return INSTANCE_STATE_UNKNOWN
        try:
            requested = self._request(latest_state)
        except slapos.slap.ServerError:
            self._logger.exception('Got an error requesting partition for '
                'its state')
            return INSTANCE_STATE_UNKNOWN
        part_id = requested.getId()
        self._logger.debug('part_id = %r', part_id)
        if not part_id:
            # Master did not allocate a partition yet.
            return INSTANCE_STATE_UNKNOWN
        return INSTANCE_STATE_DICT[self._retryRPC(
            GET_PARTITION_STATE_METHOD_ID,
            (self.computer_guid, part_id)
        )]

    def install(self):
        """
        Make software available on computer.
        """
        self._supply('available')

    def uninstall(self):
        """
        Make software unavailable on computer.
        """
        self._supply('destroyed')

    def start(self):
        """
        Request started instance (or starting existing one)
        """
        self._request('started')
    request = start

    def stop(self):
        """
        Request stopped instance (or stopping existing one).
        """
        self._request('stopped')

    def destroy(self):
        """
        Destroy existing instance.
        """
        self._request('destroyed')

    def teardown(self):
        """
        Interrupt a running test sequence, putting it in idle state.
        """
        if self.request_kw is not None:
            self.destroy()
        self.uninstall()
        self.state = TESTER_STATE_INSTANCE_UNISTALLED

    def tic(self, now):
        """
        Check for missed deadlines (-> test failure), conditions for moving to
        next state, and actually moving to next state (executing its payload).
        """
        deadline = self.deadline
        if deadline < now and deadline is not None:
            raise TestTimeout(self.state)
        _, _, state, software_state, instance_state = self.transition_dict[
            self.state]
        if (software_state is None or
                software_state == self._getSoftwareState()) and (
                instance_state is None or
                instance_state == self._getInstanceState()):
            if state is None:
                return None
            self._logger.debug('Going to state %i (%r, %r)', state,
                software_state, instance_state)
            self.state = state
            step, delay, _, _, _ = self.transition_dict[state]
            self.deadline = now + delay
            getattr(self, step)()
        return self.deadline

def main():
    """
    Note: This code does not test as much as it monitors.
    The goal is to regularily try to build & instanciate a software release
    on several machines, to monitor vifib stability and SR stability as time
    passes (and things once available online become unavailable).
    Part of this function could be reused to make an actual test bot, testing
    only when actual changes are committed to a software release, to look for
    regressions.

    Note: This code does not connect to any instanciated service, it relies on
    the presence of a promise section to make instanciation fail until promise
    is happy.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--pidfile', '-p', help='pidfile preventing parallel '
        'execution.')
    parser.add_argument('--log', '-l', help='Log file path.')
    parser.add_argument('--verbose', '-v', help='Be verbose.',
        action='store_true')
    parser.add_argument('configuration_file', type=argparse.FileType(),
        help='Slap Test Agent configuration file.')
    # Just to keep strong references to AutoSTemp instances
    key_file_dict = {}
    def asFilenamePair(key, cert):
        # Note: python's ssl support only supports fetching key & cert data
        # from on-disk files. This is why we need to "convert" direct data
        # into file paths, using temporary files.
        cert = cert.strip()
        try:
            temp_key, temp_cert = key_file_dict[cert]
        except KeyError:
            temp_key = AutoSTemp(key.strip())
            temp_cert = AutoSTemp(cert)
            key_file_dict[cert] = (temp_key, temp_cert)
        return temp_key.name, temp_cert.name
    args = parser.parse_args()
    pidfile = args.pidfile
    if pidfile:
        setRunning(pidfile)
    try:
        log = args.log
        formatter = logging.Formatter('%(asctime)s %(message)s')
        logger = logging.getLogger()
        if args.verbose:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        if log:
            handler = logging.FileHandler(log)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            log_file = open(log)
            log_file.seek(0, 2)
        section_dict = {}
        configuration = ConfigParser.SafeConfigParser()
        configuration.readfp(args.configuration_file)
        for section in configuration.sections():
            if section == 'agent':
                continue
            section_dict[section] = section_entry_dict = dict(
                configuration.items(section))
            for key in ('request_kw', 'max_install_duration',
                        'max_destroy_duration', 'max_request_duration',
                        'max_uninstall_duration', 'computer_list',
                    ):
                if key in section_entry_dict:
                    section_entry_dict[key] = json.loads(
                        section_entry_dict[key])
            if 'key' in section_entry_dict:
                key_file, cert_file = asFilenamePair(section_entry_dict['key'],
                    section_entry_dict['cert'])
                section_entry_dict['key'] = key_file
                section_entry_dict['cert'] = cert_file
        agent_parameter_dict = dict(configuration.items('agent'))
        # XXX: should node title be auto-generated by installation recipe ?
        # For example, using computer guid.
        node_title = agent_parameter_dict['node_title']
        test_title = agent_parameter_dict['test_title']
        project_title = agent_parameter_dict['project_title']
        parallel_task_count = int(agent_parameter_dict.get('task_count', 1))
        task_distribution_tool = TaskDistributionTool(agent_parameter_dict[
            'report_url'])
        master_slap_connection_dict = {}
        test_result = task_distribution_tool.createTestResult(
            revision='',
            test_name_list=section_dict.keys(),
            node_title=node_title,
            allow_restart=True,
            test_title=test_title,
            project_title=project_title,
        )
        test_result.watcher_period = 60
        if log:
            test_result.addWatch(log, log_file, max_history_bytes=10000)
        assert test_result is not None
        ran_test_set = set()
        running_test_dict = {}
        more_tests = True
        while True:
            # Get up to parallel_task_count tasks to execute
            while len(running_test_dict) < parallel_task_count and \
                    more_tests:
                test_line = test_result.start(
                    exclude_list=list(ran_test_set))
                if test_line is None:
                    more_tests = False
                    break
                test_name = test_line.name
                try:
                    section_entry_dict = section_dict[test_name]
                except KeyError:
                    # We don't know how to execute this test. Assume it doesn't
                    # exist anymore, and fail it in result.
                    test_line.stop(stderr='This test does not exist on test '
                        'node %s' % (node_title, ))
                    continue
                master_url = section_entry_dict['master_url']
                master_slap_connection_key = (master_url,
                    section_entry_dict.get('key'))
                try:
                    supply, order, rpc = master_slap_connection_dict[
                        master_slap_connection_key]
                except KeyError:
                    key = section_entry_dict.get('key')
                    cert = section_entry_dict.get('cert')
                    slap = slapos.slap.slap()
                    slap.initializeConnection(master_url, key, cert)
                    supply = slap.registerSupply()
                    order = slap.registerOpenOrder()
                    assert master_url.startswith('https:')
                    rpc = xmlrpclib.ServerProxy(master_url, allow_none=True,
                        transport=x509Transport(
                            {'key_file': key, 'cert_file': cert}))
                    master_slap_connection_dict[
                        master_slap_connection_key] = (supply, order, rpc)
                tester = SoftwareReleaseTester(
                    test_name + '_' + node_title + time.strftime(
                        '_%Y/%m/%d_%H:%M:%S_+0000', time.gmtime()),
                    logger,
                    rpc,
                    supply,
                    order,
                    section_entry_dict['url'],
                    random.choice(section_entry_dict['computer_list']),
                    section_entry_dict['max_install_duration'],
                    section_entry_dict['max_uninstall_duration'],
                    section_entry_dict.get('request_kw'),
                    section_entry_dict.get('max_request_duration'),
                    section_entry_dict.get('max_destroy_duration'),
                )
                ran_test_set.add(test_name)
                running_test_dict[test_name] = (test_line, tester)
            if not running_test_dict:
                break
            now = time.time()
            # Synchronise refreshes on watcher period, so it doesn't report a
            # stalled test node where we are actually still sleeping.
            # Change test_result.watcher_period outside this loop if you wish
            # to change sleep duration.
            next_deadline = now + test_result.watcher_period
            for section, (test_line, tester) in running_test_dict.items():
                logger.info('Checking %s: %r...', section, tester)
                try:
                    deadline = tester.tic(now)
                except Exception:
                    logger.exception('test failed')
                    test_line.stop(
                        test_count=1,
                        error_count=1,
                        failure_count=0,
                        skip_count=0,
                        stderr=traceback.format_exc(),
                    )
                    del running_test_dict[section]
                    try:
                        tester.teardown()
                    except Exception:
                        logger.exception('teardown failed, human '
                            'assistance needed for cleanup')
                        raise
                else:
                    logger.info('%r', tester)
                    if deadline is None:
                        # TODO: report how long each step took.
                        logger.info('Finished !')
                        test_line.stop(
                            test_count=1,
                            error_count=0,
                            failure_count=0,
                            skip_count=0,
                        )
                        del running_test_dict[section]
                    else:
                        next_deadline = min(deadline, next_deadline)
            if running_test_dict:
                to_sleep = next_deadline - time.time()
                if to_sleep > 0:
                    logger.info('Sleeping %is...', to_sleep)
                    time.sleep(to_sleep)
                if not test_result.isAlive():
                    for _, tester in running_test_dict.itervalues():
                        tester.teardown()
    finally:
        if pidfile:
            setFinished(pidfile)
        # Help interpreter get rid of AutoSTemp instances.
        key_file_dict.clear()

if __name__ == '__main__':
    main()
