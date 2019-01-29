# Walkthroughs

This document contains a series of walkthroughs, starting from the most simple case and moving into more complex scenarios.

## Setting up IoTEdge for running E2E tests

Even if you have IoTEdge installed on a linux VM, you still need to run some configuration scripts to prepare for running our E2E tests.

Warning: These scripts will update your IoTEdge instance.  In particular, if you have device identities that you want to preserve, you may want to back up the contents of your /etc/iotedge/config.yaml before you run through this process.

The setup process is already documented in the README.md document at the root of the edge_e2e project.  The walkthrough here is the quick version.
### Step 1: get these environment variables from the keyvault or from a friend:
* `IOTHUB_E2E_REPO_ADDRESS`
* `IOTHUB_E2E_REPO_USER`
* `IOTHUB_E2E_REPO_PASSWORD`

If you want to run a private build of the edgeHub and edgeAgent containers, you need to set these variables
* `IOTHUB_E2E_EDGE_PRIVATE_REGISTRY`
* `IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE`
* `IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE`

Also, set `IOTHUB_E2E_CONNECTION_STRING` to the IotHub instance you want to use for your tests.

### Step 2: run edge-e2e/scripts/setup_ubuntu.sh

You need to run this script even if you're already running IoTEdge.  This script was written so it can be called multiple times without causing damage.

This script:
1) Sets up Python 3.6 and makes sure that it gets called with the `python` command.
2) Sets up the Moby container runtime.
3) Installs the IoTEdge daemon
4) Starts up a private Docker container registry inside of a Docker container
5) Pre-fetches some container images

### Step 3: create IoTEdge device and deploy default containers

Even if you've already created IoTEdge devices, you're better off using this script to create a new one.  Every time you run his script, you create new registry identities.

Run `edge-e2e/scripts/create_new_edgehub_device.sh`.  This will create new registry identities for your IotEdge device along with a registry identity for a friend device that is used by the test scripts.  It edits config.yaml to insert the device connection string for you, deploys a default set of modules, and restarts the iotedge daemon.

After this script is run, iotedge should be running with 4 modules: `edgeAgent`, `edgeHub`, `nodeMod`, and `friendMod`.  `nodeMod` and `friendMod` both use a known good build of the node.js test wrappers.  The intention is that `nodeMod` will be used as an SDK-under-test for your initial runs, but will soon be replaced by whatever SDK code you with to test.  `friendMod`, on the other hand, will not be replaced.  It will always use a known-good build of the node.js wrappers.  Its purpose is to act as "the other actor" for a bunch of the tests.  So, for instance, if a test needs to send an event to another module, `friendMod` will be that other module.  Likewise, if your wrapper is missing an implementation (like `deviceClient` or `eventHubClient`), the test scripts will use `friendMod` to instantiate those objects.  So, for example, if your wrapper implements `deviceClient`, the test case `test_device_method_from_module_to_friend_device` will use your SDK wrapper for the deviceClient object that receives the device method call.  If your SDK does not implement deviceClient,the test scripts will use the node.js implementation of deviceClient for the object that receives the method call.

## List of possible test scenarios

The Edge E2E tests is a suite of tests that exercise module functionality which can run against any language SDK under 6 possible scenarios:
1) AMQP against IoTHub
2) AMQP-WS against IoTHub
3) MQTT against IoTHub
4) MQTT-WS against IoTHub
5) AMQP against EdgeHub
6) MQTT against EdgeHub

When tests are run against IoTHub, the following things happen:
1) Test cases are skipped if the functionality isn't supported when connecting directly to IoT hub (such as output events and method invoke)
2) The `moduleClient` is created using a connection string, and this connection string does not include a `GatewayHostName` value.
3) Even though we're not connecting through `EdgeHub`, we run using the wrapper that is running inside the container that is being _managed_ by IoTEdge.

Point #3 may be confusing because we're using code that is inside an IoTEdge container, but we are not connecting that code to IoTEdge.  A more sensible architecture would have us running this code in a container that is completely decoupled from IoTEdge, but that's not what we have today.  It is safe to say, however, that the fact that IoTEdge is managing the lifetime of our test wrapper doesn't impact the tests if we're not connecting that container through `edgeHub`.

When tests are run against EdgeHub, the following happens:
1) A full set of tests is executed.  There may be one or two test cases skipped because of transient bugs, but this should be considered an exception rather than the rule.
2) The `moduleClient` is connected using the IoTEdge HSM environment (formerly known as "edgelet" and "edge daemon")

There is one other sceanrio that we can run, which is testing code through edgeHub, but outside of an IoTEdge container.  This is used primarily for debugging.  In this case, we connect with a connection string that includes the `GatewayHostName` value, and a CA certificate which was manually extracted from the edge environment.  This functionality is enabled when we pass the `--local` option on the `pytest` command line.

## Different ways to configure and run the tests

The first way to run tests is using the scripts in the `edge-e2e/scripts` folder.  These scripts give you some power surrounding the actual test run.
1) They can take a set of build parameters (language, repo, base branch, and commit/pull request ID) and create a module container that is running that code.
2) They can automatically deploy whatever containers you want to test against (a known-good container for each language, or a privately built container)
3) They can provide a set of clear container logs, as text files, that begin when the test starts and end when the test ends.  They can also log the `pytest` output and provide result files in `JUnit`-compatible XML format.
4) They can run all 6 scenarios (above) in series and provide 6 sets of output files (logs and result files) cleanly organized by scenario name.
5) They can provide a cleaner execution environment by restarting `iotedged` at the beginning of a test run (before the set of 6 starts) and by restarting the modules at the beginning of each scenario.
6) They _must_ be run from a `bash` prompt on the same machine that hosts your IoTEdge instance.

The second way to run tests is to call pytest manually inside the `edge-e2e/test-runner` folder.
1) This assumes that your test container has already been build and deployed.
2) It does not provide log files in any clean format and does not produce `JUnit` results
3) It only runs a single scenario
4) It is able to run a subset of tests
5) It is able to run using code inside a local debugger instead of running against a container (handy for debugging).
6) It is able to test against IoTHub or `edgeHub`, using connection string and extracted CA (if needed)
7) It can be run from a Linux bash prompt or a Windows command prompt on any machine.  It does not need to be run on the machine that hosts your IoTEdge instance.  (though, if it testing communication through edgeHub, it will need to be able to connect _through_ your IoTEdge instance.)

The walkthroughs below cover some of the more common possible scenarios that you could run, but this is not the full list of possibilities.

## Walkthrough #1: Running your first set of E2E tests (one scenario) using a pre-built container
To run this walkthrough, we will use the bash scripts in `edge-e2e/scripts` to deploy our containers and we'll run the full set of tests by calling pytest manually.

1) use edge-e2e/scripts/deploy-test-container.sh to deploy your container by specifying the language that you want to deploy as a double-dash option (e.g. `--c` for c and `--python` for python). Ex.:

`edge-e2e/scripts/deploy-test-container.sh --c`

This script will also automatically deploy the friend module, which is always used for testing module-to-module communication.  Note: if this is the first time you're using a particular LKG module, it may take a while for the edgeAgent to download and start the module (perhaps up to 10 minutes).  You should not continue with the next step until you use the `iotedge` or `docker` CLI tools to verify that the module is running.

```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/scripts$ ./deploy-test-containers.sh --c
Operating with device bertk-edge-ga-6_bertk_550 on on hub bertk-edge.azure-devices.net

Deploying the following containers:
    friend: bertkcontainers.azurecr.io/edge-e2e-node6
        c: bertkcontainers.azurecr.io/edge-e2e-gcc
{
  "$edgeAgent": {
<--snip-->
```

2) Verify that your module is running.  In this example, we can see that cMod is running, so we're good to continue:

`iotedge list`

```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/scripts$ iotedge list
NAME             STATUS           DESCRIPTION      CONFIG
cMod             running          Up 14 minutes    bertkcontainers.azurecr.io/edge-e2e-gcc
friendMod        running          Up 2 days        bertkcontainers.azurecr.io/edge-e2e-node6
edgeHub          running          Up 2 days        mcr.microsoft.com/azureiotedge-hub:1.0
edgeAgent        running          Up 2 days        mcr.microsoft.com/azureiotedge-agent:1.0
```

1) run pytest inside the edge-e2e/test-runner folder.  Here are some examples:

| command line | meaning |
|---|---|
| `pytest --csharp-wrapper` | Use the csharp module to run against `edgeHub` (the default) using MQTT (the default). |
| `pytest --c-wrapper--direct-to-iothub --transport=amqpws` | Use the C module to test against IoTHub using AMQP with websockets |
| `pytest --java-wrapper --transport=amqp` | Use the Java module to test against edgeHub (the default) using AMQP |

At the end of the run, you will see your results.

```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/test-runner$ pytest --node-wrapper --transport=amqp
========================== test session starts ==========================
platform linux -- Python 3.6.5, pytest-3.8.0, py-1.6.0, pluggy-0.7.1 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/bertk/repos/iot-sdks-e2e-fx/test-runner, inifile: pytest.ini
plugins: timeout-1.3.2
<--snip-->
test_module_twin_reported_properties.py::test_module_can_set_reported_properties_and_service_can_retrieve_them PASSED       [100%]

========================== 29 passed in 173.71 seconds ==========================
Exception ignored in: <bound method ApiClient.__del__ of <swagger_client.api_client.ApiClient object at 0x7f50fb4b5c88>>
Traceback (most recent call last):
<--snip-->
```

An aside: If something goes wrong, you can see what is happening by looking at the docker logs (e.g. `docker logs -f cMod `)

The line "29 passed" is the important information.  The Exception that happens after the run is complete can be ignored.

## Walkthrough #2: Running a full set of E2E tests (all six scenarios) using a custom container

This walkthrough is the most simple.  It uses the toplevel Jenkins (actually VSTS) script to build a container and run all tests against it.

To run this, call `edge-e2e/scripts/ci-e2e-toplevel.sh` and pass your build parameters.  You can call this script with no parameters for usage instructions.  One of the benefits of his script is that it will build, deploy, wait for deployment, and run all scenarios without any interaction.

```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/scripts$ ./ci-e2e-toplevel.sh --language node --repo Azure/azure-iot-sdk-node --branch master --commit master
AZURE_REPO=Azure/azure-iot-sdk-node
BRANCH_TO_MERGE_TO=master
Building with commit master
<--snip-->
FINAL RESULTS:


SUCCEEDED: iothub amqp node
SUCCEEDED: iothub amqpws node
SUCCEEDED: iothub mqtt node
SUCCEEDED: iothub mqttws node
SUCCEEDED: edgehub amqp node
FAILED: edgehub mqtt node
ci-run-all.sh failed
```

In this example, my run using MQTT against edgeHub failed.  To find the logs for the failure, I can look in the `edge-e2e/results/edgehub-node-mqtt` folder.

Once you run this step, you can run `docker ps` or `iotedge list` to see that you're using your private container.  If you want to continue with this container, you can run pytest manually or run whatever tools you want.

In this example, `friendmod` is using `bertkcontainers.azurecr.io/edge-e2e-node6` which is an LKG container, and nodeMod is using `localhost:5000/node-test-image:latest`.  `localhost:5000` is the private repository that is running inside the docker container named `repository` and `node-test-image` is the name of the image that was built as part of the `ci-e2e-toplevel.sh` script.

(The `bertkcontainers` container repository should be moved and/or renamed, but that's a different story)

```
bertk@bertk-edge-ga-6:~/repos/internals$ iotedge list
NAME             STATUS           DESCRIPTION      CONFIG
edgeHub          running          Up 18 hours      mcr.microsoft.com/azureiotedge-hub:1.0
friendMod        running          Up 18 hours      bertkcontainers.azurecr.io/edge-e2e-node6
nodeMod          running          Up 18 hours      localhost:5000/node-test-image:latest
edgeAgent        running          Up 18 hours      mcr.microsoft.com/azureiotedge-agent:1.0
```

## Walkthrough #3: Running a single test case inside a container

Running a single test inside of a container is just as easy as running an entire scenario and very similar to Walkthrough #1 above.  Once your container is deployed (either LKG, like Walkthrough #1, or custom built, like Walkthrough #2), you just need to pass the filename for the test case and possibly the name of the test case along with the pytest command line.

All of the tests are inside the `edge-e2e/test-runner` folder.  All modules with tests inside are named with a `test_` prefix, and all test cases are inside those files as functions that are named with `test_` prefixes.

If you want to run the tests in a single .py module, you would call `pytest` passing the name of the .py file as follows
```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/test-runner$ pytest --node-wrapper --transport=amqp test_module_send_telemetry.py
================================================= test session starts ==================================================
<--snip-->
test_module_send_telemetry.py::test_module_send_event_to_iothub PASSED                                           [100%]

=============================================== 1 passed in 3.57 seconds ===============================================
```

If you want to run a single test, use the test_file_name.py::test_function_name syntax as follows:
```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/test-runner$ pytest --node-wrapper --transport=amqp test_module_twin_desired_properties.py::test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events
================================================= test session starts ==================================================
<--snip-->
test_module_twin_desired_properties.py::test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events PASSED [100%]

=============================================== 1 passed in 5.65 seconds ===============================================
```

If you want to add additional debug spew from the test _script_, you can pass `-s` to pytest.  Note: this will only give you output from the test runner.  If you want output from the SDK code, you will need to inspect the docker logs for that container.

## Walkthrough #4: Running a scenario using code running inside a debugger

Running your SDK code inside of a debugger is almost as easy as running inside of a container, but you have to do some pre-configuration because you'll have the following configuration.  Note, this configuration assumes that your debugger is running on the Windows machine that hosts your IoTEdge VM.  This machine layout isn't technically required, but it's easy and it's the only configuration I've ever personally used.  It's possible to run your debugger on a different physical machine, but you _may_ need to do some extra network configuration to expose the correct ports from your IoTEdge machine, including getting them through your firewall.

Host Machine: Windows
* Hosts the Linux VM that's running IoTEdge under Hyper-V
* Runs debugger with SDK wrapper
* Runs test scripts (from `edge-e2e/test-runner`) via `pytest` from command line.
* SDK wrapper connects to edgeHub instance on Linux VM via environment variables (connection string and CA certificate)

Client VM: Linux
* Runs IoTEdge daemon and IoTEdge containers
* Container for the SDK that you're debugging is technically running (it shows up in `iotedge info`), but inert (not connected to edgeHub)
* Containers for `friendMod`, `edgeHub`, and `edgeAgent` are still running and active inside the IoTEdge container environment.

These steps assuming you've already called `create-new-edgehub-device.sh` to configure your IotEdge instance.

1. Make sure you have Python 3.6 installed on your Windows machine and in the path along with the scripts folder.  Since my machine doesn't have Python3.6 always in the path, I use `set path=%path%;c:\Python36;c:\Python36\scripts`
   If you need to verify your Python install, you should verify both python and pip as follows.  The version of python might be slightly different, but it should be OK as long as it's 3.6.x+.  The version of pip is less important, but it should have the `(python 3.6)` info at the end.

```
F:\repos\iot-sdks-e2e-fx\test-runner>python --version
Python 3.6.3

F:\repos\iot-sdks-e2e-fx\test-runner>pip --version
pip 18.0 from c:\python36\lib\site-packages\pip (python 3.6)
```

2. Clone the `iot-sdks-e2e-fx` repo on your Windows machine. 
3. On your Windows machine, go to the `test-runner` folder. Run `pip install -r requirements.txt`.  This will grab the various python libraries that the test runner needs.
4. On your Linux machine, run `edge-e2e/scripts/get-environment.sh windows`.  This gives you some handy text that you can copy/paste into your Windows environment to point the test runner at your Linux IoTEdge instance.
```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/scripts$ ./get-environment.sh windows
@rem Set the following values in your environment:
@rem Environment for with device bertk-edge-ga-6_bertk_550 on on hub bertk-edge.azure-devices.net
@rem device_connection_string: "<REDACTED>"
set IOTHUB_E2E_CONNECTION_STRING=<REDACTED>
set IOTHUB_E2E_EDGEHUB_DNS_NAME=<REDACTED>
set IOTHUB_E2E_EDGEHUB_DEVICE_ID=<REDACTED>
set IOTHUB_E2E_EDGEHUB_CA_CERT=<REDACTED>
```

(The CA_CERT value will be a long Base64-encoded string)

5. On your Windows machine, make sure the environment variables from Step 4 are set in whatever environment you're going to run pytest from.  It does not need to be set in your debugger environment.  pytest will fail quickly if these variables are missing.

6.  On you Linux machine, make sure the container for your SDK is deployed.  Again, this container is inert, but it still needs to be present because the test runner needs it to exist as a module in the IoTHub registry.  Again, it may take a while to download the Docker container image if this is the first time using it.  Don't continue until your module (e.g. `javaMod`) shows up as `running` when you run `iotedge list`.

```
bertk@bertk-edge-ga-6:~/repos/iot-sdks-e2e-fx/scripts$ ./deploy-test-containers.sh --java
Operating with device bertk-edge-ga-6_bertk_550 on on hub bertk-edge.azure-devices.net

Deploying the following containers:
    friend: bertkcontainers.azurecr.io/edge-e2e-node6
      java: bertkcontainers.azurecr.io/edge-e2e-java8
{
<--snip-->
```

7.  As a test of your test-runner environment, you can run tests using the deployed container.  If you need to debug this, remember you're running with the test script on your Windows box, but the code that you're testing is still inside the deployed container.  Use `docker logs` on the containers or call `pytest` with `-s`

Note the values printed by `pytest` as `Run Parameters`.  In particular, the test_module_uri below is `http://bertk-edge-ga-6:8080`.  This tells us that your code under test is exposing a REST endpoint on this URI, which happens to be on my Linux VM

```
F:\repos\internals\edge-e2e\test-runner>pytest --node-wrapper --local test_module_send_telemetry.py
============================= test session starts =============================
platform win32 -- Python 3.6.3, pytest-3.6.1, py-1.5.3, pluggy-0.6.0 -- c:\python36\python.exe
<--snip-->
Run Parameters:
  module_id:            nodeMod
  friend_module_id:     friendMod
  friend_device_id:     bertk-edge-ga-6_bertk_550_friend
  test_module_uri:      http://localhost:8080 (module under test)
  friend_module_uri:    http://bertk-edge-ga-6:8099 (friend container)
  friend_device_uri:    http://localhost:8080 (module under test)
  registry_uri:         http://localhost:8080 (module under test)
  service_client_uri:   http://localhost:8080 (module under test)
  eventhub_uri:         http://bertk-edge-ga-6:8099 (friend container)
  using environment:    True
  test transport:       mqtt
  friend transport:     mqtt
  straight to iothub:   False
collected 1 item
test_module_send_telemetry.py::test_module_send_event_to_iothub FAILED   [100%]

================================== FAILURES ===================================
______________________ test_module_send_event_to_iothub _______________________
test_module_send_telemetry.py:34: in test_module_send_event_to_iothub
    received_message = input_thread.get(test_utilities.default_eventhub_timeout)
c:\python36\lib\multiprocessing\pool.py:640: in get
    raise TimeoutError
E   multiprocessing.context.TimeoutError
---------------------------- Captured stdout setup ----------------------------
```

Of particular interest here is the fact that the test failed with a timeout error.  There are two different ways this could have happened:
* The test runner could not communicate with the wrapper code exposed from the `test_module_uri` as shown above.  This could be a stalled container, a badly configured firewall, a bad Windows environment, or any other of a number of things.
* The test runner could be communicating with the wrapper, but some operation just happened to time out.

In the case of #1, there would be thread dumps for every thread inside Python.exe, like 90 or so.  In the case of #2, the output is short and sweet and shows you two things:
* In the first failure text above, it shows that there was a failure on line 34 of test_module_send_telemetry.py.  If you look at this code, it's in the middle of the test script, long after the connections have been established.  (so there's no problem connecting from the test runner to the wrapper).
* Lower in the output, there's output from the pytest script stdout stream during the test.  This output corresponds directly to print() calls inside test_module_send_telemetry.py.

```
---------------------------- Captured stdout call -----------------------------
connecting module client
connecting eventhub client
enabling telemetry on eventhub client
start waiting for events on eventhub
sending event: MWM4DIRY0FP3WZBIF3IQU6QN3OZO8RU61S8A23WVE1HR7RGCUYL3EJSEL1AVSYJU
wait for event to arrive at eventhub
-------------------------- Captured stdout teardown ---------------------------
```

8. Now that you've verified your test runner is configured correctly, you can launch your wrapper inside of your debugger.  This depends on which SDK you're using, and it's subject to change, but, in short:
* Node: after running `lerna run build` as usual, run `azure-iot-sdks-node\edge-e2e\wrapper\nodejs-server-server\index.js`
* C: run `azure-iot-sdks-c\edge-e2e\build.cmd`, then open `azure-iot-sdks-c\edge-e2e\cmake\Project.sln` inside Visual Studio.  The sub-project that you want to debug is named `edge_e2e_rest_server`.
* Java: open `azure-iot-sdks-java\pm.xml` in your favorite debugger.  Launch `edge-e2e\src\main\java\Main.java`
* C#: TODO
* Python: TODO

When you launch the app, it will open a RESTAPI endpoint on some port.  The test script will know which one.  Some SDKs display the port to stdout, and some don't.

9.  Run pytest against the code in your debugger by passing the `--local` flag along with whatever other flags you need.  This flag does two things:
* It changes the `test_module_uri` to the appropriate port on `http://localhost`
* It connects to edgeHub using connection string and CA instead of getting the trust bundle from the iotedge HSM.
You can verify that the test runner is configured correctly by looking at the `test_module_uri` that pytest gives you.

```
F:\repos\internals\edge-e2e\test-runner>pytest --node --local test_module_methods.py
<--snip-->
  test_module_uri:      http://localhost:8080 (module under test)
<--snip-->
========================== 4 passed in 18.14 seconds ==========================
```

