
# Test Script Organization

Like the wrappers, the test script also has some swagger.io codegen libraries.  Unlike the wrappers, we are only using the codegen library.  We don't need to change it from what we get from swagger.io tools.

## edge-e2e\\test-runner\\

Structure of `test-runner` directory:

- `conftest.py` - configuration information
- `environment.py` - constants related to how the tests are being run
- `connections.py` - functions for connecting to the RESTapi surfaces of SDK wrappers and for connecting to the different iothub services.  This file, for instance, is where we decide (based on environment.py) if we call ModuleClient.fromConnectionString or if we call ModuleClient.fromEnvironment
- `module_api.py`, registry_api.py, service_api.py, and eventhub_api.py has wrappers that make the swagger library a little easier to consume.  Tests (almost) never construct these object directly.  They almost always get them connections.py
- `test_connect_disconnect.py` **the most basic set of tests**.  It connects and disconnects to the various services.  It's probably the first test you will run.
- `test_module_*.py` the individual feature tests
- `test_utility.py` utility functions that the tests can use