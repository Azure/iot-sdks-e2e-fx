# Aspirational Fault Injection Roadmap

## Remove code duplication between regular and fault injection edge tests

Currently, the folders are set up where we have:
```
test-runner
|
|-- module_tests
|   |
|   |-- test_connect_disconnect.py 
|   `-- ...
`-- module_fi_tests
    |
    |-- test_connect_disconnect_fi.py
    `-- ...
```

This is all fine except when one developer makes a change in the main fault tests and that change then causes a break because the code in the fault injection folder becomes out of sync. To fix this there is a proposal to leverage Python Fixtures to programmatically specify which blocks of code to run depending on the edge e2e scenario (edgehub, fault injection, iothub...). 

A link to pytest fixtures, which are the proposed mechanism for implementation, is here: https://docs.pytest.org/en/latest/fixture.html

So then the folders would be set up like this:
```
test-runner
|
|-- test_connect_disconnect.py
|-- test_module_twin_blah_blah.py
`-- ...
```

For each test case, only one test, and within the tests PyTest Fixtures would be used so we could specify which codepaths to follow.

## Expand Types of Faults

Currently, only one type of fault is created using the framework. Using the standard Edge E2E APIs and the PyDocker API, the framework provides a low resolution, simple way to inject faults. Essentially at certain points during the typical tests (e.g. sending telemetry from edge module) the fault injection tests use the PyDocker API to disable the network connection around the EdgeHub Docker container. Then the connection is reestablished and the reconnection from the module is validated somehow (e.g. telemetry is received after a disconnect on an eventhub endpoint). 

The future goal will be to expand the type of faults created through the fault injection test. For instance: 

- using PyDocker to restart the EdgeHub Container (breaking the edge module's connection to it)
- using PyDocker to destroy the EdgeHub Container, then having it revive either manually using PyDocker or automatically by the EdgeAgent
- Delaying the time between when the fault starts and when it ends, e.g. for 10 seconds, the edge module is trying to multiple telemetry messages but cannot connect to EdgeHub. After the 10 seconds the connection is reestablished and the edge module attempts to reconnect and send the queued messages. 
