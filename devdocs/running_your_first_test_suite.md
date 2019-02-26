# Running your first test suite

These instructions will download some test containers and run a suite of tests on a container

## Step 1: Pre-cache containers

To validate your framework and your environment configuration (especially the `IOTHUB_E2E_REPO*` environment variables), follow these steps.

### First, log into our docker repository.

*What this accomplishes*: This gives the currently logged-in user the ability to push and pull docker images.  These images contain everything necessary to call SDK functions from the test framework.  This also lets us verify that the 3 `IOTHUB_E2E_REPO_*` environment variables are set correctly.

*Command to run*: `docker login -u $IOTHUB_E2E_REPO_USER -p $IOTHUB_E2E_REPO_PASSWORD $IOTHUB_E2E_REPO_ADDRESS`

*Example output*:
```
bertk@bertk-test-vm:~$ docker login -u $IOTHUB_E2E_REPO_USER -p $IOTHUB_E2E_REPO_PASSWORD $IOTHUB_E2E_REPO_ADDRESS
WARNING! Using --password via the CLI is insecure. Use --password-stdin.
WARNING! Your password will be stored unencrypted in /home/bertk/.docker/config.json.
Configure a credential helper to remove this warning. See
https://docs.docker.com/engine/reference/commandline/login/#credentials-store

Login Succeeded
bertk@bertk-test-vm:~$
```

### Then, pull one of our test images:

*What this accomplishes*: This pulls a known-good image with the Node.js sdk.  This known-good image is used by Horton as the friendModule image (which provides helper functions for testing the SDK), and, later on, we're also going to use this image as the module-under-test.  Having the same Node.JS module for the  test module and also for the friend module means that test cases which use module-to-module communication will talk between one node.js module (the test module) and a different node.js module (the friend module).

*Command to run*: `docker pull $IOTHUB_E2E_REPO_ADDRESS/edge-e2e-node6:latest`

*Example output*:
```
bertk@bertk-test-vm:~$ docker pull $IOTHUB_E2E_REPO_ADDRESS/edge-e2e-node6:latest
latest: Pulling from edge-e2e-node6
a5a6f2f73cd8: Pull complete
6fd77ab8da06: Pull complete
807d721c52c2: Pull complete
0836be6d1865: Pull complete
08d96d706d9b: Pull complete
1cc6ab527bbf: Pull complete
cebade96c2f0: Pull complete
969d3279f37e: Pull complete
645cf17ae46c: Pull complete
efcab7795552: Pull complete
37b9d1f93f30: Pull complete
ec18f2a5ecac: Pull complete
6d3f537e3b70: Pull complete
56844f8fe141: Pull complete
5e7accbc2e38: Pull complete
c366cca0a4d5: Pull complete
Digest: sha256:a04aefe984c18f4636d3a53f74d33b6c9d7937b568ed34d34b66a04148662e8f
Status: Downloaded newer image for <REDACTED>/edge-e2e-node6:latest
<REDACTED>/edge-e2e-node6:latest
bertk@bertk-test-vm:~$
```

## Step 2: Create an IoT Edge instance and deploy it to our VM using the containers we just downloaded

### Next: Create a new IoT Edge device instance and deploy it to our box:

*What this accomplishes*: This creates an IoTEdge identity in our IoTHub instances.  It pre-populates that IoTEdge identity with a single model, and, it deploys that IoTEdge identity to our VM.

*Command to run*: `scripts/create-new-edgehub-device.sh`

*Example output*:
```
bertk@bertk-test-vm:~/repos/e2e-fx$ scripts/create-new-edgehub-device.sh
scripts
Creating new device on hub bertk-edge.azure-devices.net
creating device bertk-test-vm_bertk_76547905
creating device bertk-test-vm_bertk_76547905_leaf_device
updating config.yaml to insert connection string
IOTEDGE_DEBUG_LOG is not set. clearing edgeAgent RuntimeLogLevel
config.yaml updated
new edgeHub device created with device_id=bertk-test-vm_bertk_76547905
Operating with device bertk-test-vm_bertk_76547905 on on hub bertk-edge.azure-devices.net

Deploying the following containers:
    friend: <REDACTED>/edge-e2e-node6:latest
restarting iotedge
iotedge restart complete
bertk@bertk-test-vm:~/repos/e2e-fx$
```
### Then: verify deployment

It may take a while for the deployment to happen.  If you run this command and see 4 containers running, you know that it's done.  If this takes more than 3 or 4 minutes for all 4 containers to show up, something may be wrong, and you might want to investigate.

*What this accomplishes*: This verifies that the IoTEdge identity we created above has been created and deployed to this VM.

*Command to run*: `docker ps`

*Example output*:
```
bertk@bertk-test-vm:~/repos/e2e-fx$ docker ps
CONTAINER ID        IMAGE                                        COMMAND                   CREATED             STATUS              PORTS                                                                  NAMES
9bf9f9f3baf4        mcr.microsoft.com/azureiotedge-hub:1.0.6     "/bin/sh -c 'echo \"$…"   2 minutes ago       Up 2 minutes        0.0.0.0:443->443/tcp, 0.0.0.0:5671->5671/tcp, 0.0.0.0:8883->8883/tcp   edgeHub
ba2e760f0c11        <REDACTED>?/edge-e2e-node6:latest            "/usr/local/bin/node…"    2 minutes ago       Up 2 minutes        9229/tcp, 0.0.0.0:8099->8080/tcp                                       friendMod
28e7ebcce3a0        mcr.microsoft.com/azureiotedge-agent:1.0.6   "/bin/sh -c 'echo \"$…"   2 minutes ago       Up 2 minutes                                                                               edgeAgent
d7313d09359f        registry:2                                   "/entrypoint.sh /etc…"    41 minutes ago      Up 41 minutes       0.0.0.0:5000->5000/tcp                                                 registry
bertk@bertk-test-vm:~/repos/e2e-fx$
```

### Start up a module to test.

*What this accomplishes*: This script deploys a specific container that we can use for testing.  The `create_new_edgehub_device.sh` script above deployed some containers that are required for all tests, but it did not deploy the container that we're testing.

*Command to run*: `scripts/deploy-test-containers.sh --node $IOTHUB_E2E_REPO_ADDRESS/edge-e2e-node6:latest`

*Example output*:
```
bertk@bertk-test-vm:~/repos/e2e-fx$ scripts/deploy-test-containers.sh --node $IOTHUB_E2E_REPO_ADDRESS/edge-e2e-node6:latest
Operating with device bertk-test-vm_bertk_76547905 on on hub bertk-edge.azure-devices.net

Deploying the following containers:
      node: <REDACTED>/edge-e2e-node6:latest
    friend: <REDACTED>/edge-e2e-node6:latest
bertk@bertk-test-vm:~/repos/e2e-fx$
```

### Finally, verify that our test module is running.

*What this accomplishes*: This makes sure the image we just deployed is running.  Because we didn't need to pull any new images, this should show the correct results right away.  You should verify that nodeMod is running.

*Command to run*: docker ps

Example output:
```
bertk@bertk-test-vm:~/repos/e2e-fx$ docker ps
CONTAINER ID        IMAGE                                        COMMAND                   CREATED             STATUS              PORTS                                                                  NAMES
a0a8f989cb7f        <REDACTED>/edge-e2e-node6:latest             "/usr/local/bin/node…"    2 hours ago         Up 2 hours          0.0.0.0:8080->8080/tcp, 9229/tcp                                       nodeMod
9bf9f9f3baf4        mcr.microsoft.com/azureiotedge-hub:1.0.6     "/bin/sh -c 'echo \"$…"   2 hours ago         Up 2 hours          0.0.0.0:443->443/tcp, 0.0.0.0:5671->5671/tcp, 0.0.0.0:8883->8883/tcp   edgeHub
ba2e760f0c11        <REDACTED>/edge-e2e-node6:latest             "/usr/local/bin/node…"    2 hours ago         Up 2 hours          9229/tcp, 0.0.0.0:8099->8080/tcp                                       friendMod
28e7ebcce3a0        mcr.microsoft.com/azureiotedge-agent:1.0.6   "/bin/sh -c 'echo \"$…"   2 hours ago         Up 2 hours                                                                                 edgeAgent
d7313d09359f        registry:2                                   "/entrypoint.sh /etc…"    3 hours ago         Up 3 hours          0.0.0.0:5000->5000/tcp                                                 registry
bertk@bertk-test-vm:~/repos/e2e-fx$
```

## Step 3: Run a test suite with the modules we just deployed.

Now that we have all the code on our VM, let's run some tests.

### Make sure environment variables are set.

*What this accomplishes*: This is a workaround for some scripts that haven't been written yet.  In order to communicate between the leaf device and IoTEdge, we need to know the x509 certificate that IoTEdge uses to establish SSL connections.  Without this, we would get certificate errors when trying to connect the leaf device client.

*Command to run*: `eval $(scripts/get-environment.sh)` to set, followed by `echo $IOTHUB_E2E_EDGEHUB_CA_CERT` to verify the certificate is set (it should be a long base64-encoded string)

*Example output*:
```
bertk@bertk-test-vm:~/repos/e2e-fx$ eval $(scripts/get-environment.sh)
bertk@bertk-test-vm:~/repos/e2e-fx$ echo $IOTHUB_E2E_EDGEHUB_CA_CERT
LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUZTVENDQXpHZ0F3SUJBZ0lFYTR0Rlp6QU5CZ2txaGt
<MANY LINES REDACTED>
0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
bertk@bertk-test-vm:~/repos/e2e-fx$
```

### Run the NodeJs IotEdge module client tests.

*What this accomplishes*: Now that we have the test module deployed and the environment set, we can run the tests.  The fact that we're testing the node.js SDK is specified twice: once by the fact that we have the node.js image deployed, and once by the use of the --node_wrapper parameter.

*Command to run* (from `test-runner` directory): `pytest --node-wrapper -m testgroup_edgehub_module_client`

*Example output*:
```
bertk@bertk-test-vm:~/repos/e2e-fx/test-runner$ pytest --node-wrapper -m testgroup_edgehub_module_client
======================================================= test session starts ========================================================
platform linux -- Python 3.6.7, pytest-3.8.2, py-1.8.0, pluggy-0.9.0 -- /usr/bin/python3
cachedir: .pytest_cache
rootdir: /home/bertk/repos/e2e-fx/test-runner, inifile: pytest.ini
plugins: timeout-1.3.2, repeat-0.7.0
timeout: 90.0s
timeout method: signal
timeout func_only: False
collecting 44 items
Using mqtt
Using node wrapper
Adding REST adapter for TestModuleClient using the ModuleApi api at uri http://localhost:8080
Adding REST adapter for RegistryClient using the RegistryApi api at uri http://localhost:8080
Adding REST adapter for ServiceClient using the ServiceApi api at uri http://localhost:8080
Adding REST adapter for FriendModuleClient using the ModuleApi api at uri http://localhost:8099
Adding REST adapter for LeafDeviceClient using the DeviceApi api at uri http://localhost:8080
Adding direct Azure rest adapter for EventHubClient
Run Parameters:
  language:             node
  module_id:            nodeMod
  friend_module_id:     friendMod
  leaf_device_id:       bertk-test-vm_bertk_27750887_leaf_device
  using environment:    True
  test transport:       mqtt
  friend transport:     mqtt
  destination:          edgehub
PYTEST: HORTON: starting run: ['--timeout', '90', '-vv', '--showlocals', '--tb=short', '--node-wrapper', '-m', 'testgroup_edgehub_module_client']
watching edgeHub
watching friendMod
watching nodeMod
collected 44 items / 22 deselected

test_connect_disconnect.py::test_module_client_connect_disconnect PASSED                                                     [  4%]
test_connect_disconnect.py::test_module_client_connect_enable_twin_disconnect PASSED                                         [  9%]
test_connect_disconnect.py::test_module_client_connect_enable_methods_disconnect PASSED                                      [ 13%]
test_connect_disconnect.py::test_module_client_connect_enable_input_messages_disconnect PASSED                               [ 18%]
test_connect_disconnect.py::test_registry_client_connect_disconnect PASSED                                                   [ 22%]
test_connect_disconnect.py::test_service_client_connect_disconnect PASSED                                                    [ 27%]
test_connect_disconnect.py::test_device_client_connect_disconnect PASSED                                                     [ 31%]
test_connect_disconnect.py::test_device_client_connect_enable_methods_disconnect PASSED                                      [ 36%]
test_device_methods.py::test_device_method_from_service_to_leaf_device PASSED                                                [ 40%]
test_device_methods.py::test_device_method_from_module_to_leaf_device PASSED                                                 [ 45%]
test_module_input_output_loopback.py::test_module_input_output_loopback PASSED                                               [ 50%]
test_module_methods.py::test_module_method_call_invoked_from_service PASSED                                                  [ 54%]
test_module_methods.py::test_module_method_from_test_to_friend PASSED                                                        [ 59%]
test_module_methods.py::test_module_method_from_friend_to_test PASSED                                                        [ 63%]
test_module_output_routed_upstream.py::test_module_output_routed_upstream PASSED                                             [ 68%]
test_module_send_telemetry.py::test_module_send_event_to_iothub PASSED                                                       [ 72%]
test_module_to_module_routing.py::test_module_to_friend_routing PASSED                                                       [ 77%]
test_module_to_module_routing.py::test_friend_to_module_routing PASSED                                                       [ 81%]
test_module_to_module_routing.py::test_module_test_to_friend_and_back PASSED                                                 [ 86%]
test_module_twin_desired_properties.py::test_service_can_set_desired_properties_and_module_can_retrieve_them PASSED          [ 90%]
test_module_twin_desired_properties.py::test_service_can_set_multiple_desired_property_patches_and_module_can_retrieve_them_as_events PASSED [ 95%]
test_module_twin_reported_properties.py::test_module_can_set_reported_properties_and_service_can_retrieve_them PASSED        [100%]

======================================= 0 failed, 22 passed, 22 deselected in 121.33 seconds =======================================
bertk@bertk-test-vm:~/repos/e2e-fx/test-runner$
```
## Other suites to run:

### Run IoTEdge module tests with transport=amqp
*Command to run*: `pytest --node-wrapper -m testgroup_edgehub_module_client --transport=amqp`

### Run IotHub module tests with transport=mqtt-ws
Note: you have to specify iothub in two places: once in the group of tests to run (`-m testgroup_iothub_module_client`) and once in the parameter that specifies to bypas IoTEdge and go straight to IoTHub (`--direct-to-iothub`)
*Command to run*: `pytest --node-wrapper -m testgroup_iothub_module_client --transport=mqttws --direct-to-iothub`