This module is supposed to be launched from the "test" instance of a resilient
service (usually deployed using "test" software type).

One entry point, if the service has been deployed
from a "scalability" test node, so with special parameters, will automatically
communicate when the instance is started to an ERP5 TestNode Master, and start the test.

The other entry point, "bin/runStandaloneTest", is supposed to be run manually from a simple "test"
instance without special parameter (just request an instance of your software
release using the dedicated test software-type made for the occasion).
This is quite useful if you simply want to run the resiliency tests without having the whole
dedicated test infrastructure.



This module contains:
 * The code to start the test from a testnode / manually
 * A Resiliency Test Suite framework (in suites/), used to easily write new
   test suites
 * A list of test suites



TODO :
 * Check that each partition is in different slapos node.
 * Test for bang calls
 * Be able to configure from ERP5 Master (i.e from instance parameters): count of PBS/clones, then test several possibilities (so called "count" in test suite)
 * Use Nexedi ERP5, when in production.
 * Put the KVM disk image in a safe place.

------------

For reference: How-to deploy the whole test system
1/ Deploy a SlapOS Master
2/ Deploy an ERP5, install erp5_test_result BT with scalability feature (current in scalability-master2 branch of erp5.git) (currently, had to change a few lines in the scalability extension of the portal_class, should be commited)
3/ Configure 3 nodes in the new SlapOS Master, deploy in each a testnode with scalability feature (erp5testnode-scalability branch of slapos.git) with parameters like:
<?xml version="1.0" encoding="utf-8"?>
<instance>
  <parameter id="test-node-title">COMP-0-Testnode</parameter>
<parameter id="test-suite-master-url">https://zope:insecure@softinst43496.host.vifib.net/erp5/portal_task_distribution/1</parameter>
</instance>
3bis/ Supply and request http://git.erp5.org/gitweb/slapos.git/blob_plain/refs/tags/slapos-0.92:/software/kvm/software.cfg on a public node (so that vnc frontends are ok). "domain" parameter should be [ipv6] of partition. ipv4:4443 should be 6tunnelled to ipv6:4443 (Note: here, instead, I just hacked kvm_frontend to listen on ipv6).
3ter/ Supply and request http://git.erp5.org/gitweb/slapos.git/blob_plain/HEAD:/software/apache-frontend/software.cfg, with any "domain" (it won't be used), on a public node (so that web frontends are ok)
4/ On the ERP5 instance, create a project, a Task Distribution (in portal_task_distribution, type Scalability Task Distribution)
5/ On the ERP5 instance, create a Test Suite, validate it

Note: the slapos nodes are currently deployed using slapos-in-partition.
Note: you have to manually kill -10 the erp5testnode process to start deployment of test because it doesn't know when SR installation is finished.
Note: you have to manually run slapos-node-software --all on the slapos nodes if you are developping the SR you are testing.

------------
STANDALONE TESTS

Here is an example on how to deploy standalone tests on the webrunner, which means without using erp5.

1/ Deploy a SlapRunner software instance using the type test.
2/ In slapos.org, you should tell on which server you want to deploy your instances. You can adapt to your case the parameter.xml above. For the first time, you can deploy all the instances on the same node, it will run the tests faster, and it will be easier to debug :
	<?xml version='1.0' encoding='utf-8'?>
	<instance>
	  <parameter id="_">{"cluster": {"-sla-0-computer_guid": "COMP-XXXX", "-sla-1-computer_guid": "COMP-XXXX", "-sla-2-computer_guid": "COMP-XXXX"}}</parameter>
	</instance>
3/ Then go to the root instance folder : it is the one who has only "runStandaloneResiliencyTestSuite" in its bin folder.
4/ Run ./bin/runStandaloneResiliencyTestSuite and wait :) it would return "success" or "failure"
