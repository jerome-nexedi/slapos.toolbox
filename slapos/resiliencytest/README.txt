This module is supposed to be launched from the "test" instance of a resilient
service (usually deployed using "test" software type).

One entry point, if the service has been deployed
from a "scalability" test node, so with special parameters, will automatically
communicate to an ERP5 TestNode Master, and start the test.

The other entry point is supposed to be run manually from a simple "test"
instance without special parameter, and will manually run the test.



This module contains:
 * The code to start the test from a testnode / manually
 * A Resiliency Test Suite framework (in suites/), used to easily write new
   test suites
 * A list of test suites
