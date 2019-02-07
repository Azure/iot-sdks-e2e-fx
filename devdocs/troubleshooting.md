# Troubleshooting

## ./setup-ubuntu.sh Failures

### pip ImportError: cannot import name 'main'

**Sample Error:**

```
foo@foo-Virtual-Machine:~/GitRepos/edge-e2e/scripts$ ./setup-ubuntu.sh
----------------------------------------------------------
installing python 3.6
----------------------------------------------------------
Reading package lists... Done
Building dependency tree
Reading state information... Done
python3 is already the newest version (3.6.7-1~18.04).
python3-pip is already the newest version (9.0.1-2.3~ubuntu1).
0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded.
Requirement already up-to-date: pip in /home/foo/.local/lib/python3.6/site-packages (19.0.1)
~/GitRepos/edge-e2e/test-runner ~/GitRepos/edge-e2e/scripts
Traceback (most recent call last):
  File "/usr/bin/pip3", line 9, in <module>
    from pip import main
ImportError: cannot import name 'main'
pip install requirements.txt failed
setup-python36 failed
```

**Likely Cause:**

There is an incompatibility with the scripts being run and the version of pip being used. Newer versions of pip will throw this error due to syntax changes. Make sure your version of E2E-FX is not outdated. 

## ./create-new-edgehub-device.sh Failures

### HttpOperationError in get_device_connection_string

**Sample Error:**

```
foo@foo-Virtual-Machine:~/GitRepos/edge-e2e/scripts$ ./create-new-edgehub-device.sh
.
/usr/lib/python3/dist-packages/requests/__init__.py:80: RequestsDependencyWarning: urllib3 (1.23) or chardet (3.0.4) doesn't match a supported version!
  RequestsDependencyWarning)
Creating new device on hub foohub.azure-devices.net
creating device foo-Virtual-Machine_foo_259
creating device foo-Virtual-Machine_foo_259_leaf_device
updating config.yaml to insert connection string
IOTEDGE_DEBUG_LOG is not set. clearing edgeAgent RuntimeLogLevel
config.yaml updated
new edgeHub device created with device_id=foo-Virtual-Machine_foo_259
/usr/lib/python3/dist-packages/requests/__init__.py:80: RequestsDependencyWarning: urllib3 (1.23) or chardet (3.0.4) doesn't match a supported version!
  RequestsDependencyWarning)
Operating with device foo-Virtual-Machine_foo_13363547 on on hub foohub.azure-devices.net

Deploying the following containers:
    friend: iotsdke2e.azurecr.io/edge-e2e-node6
Traceback (most recent call last):
  File "./../test-runner/deploy_test_containers.py", line 60, in <module>
    hub = useExistingHubInstance(service_connection_string, edge_hub_device_id)
  File "/home/foo/GitRepos/edge-e2e/test-runner/edgehub_factory.py", line 25, in useExistingHubInstance
    return EdgeHub(service_connection_string, edge_hub_device_id)
  File "/home/foo/GitRepos/edge-e2e/test-runner/edgehub_factory.py", line 57, in __init__
    self._useExistingHub(edge_hub_device_id)
  File "/home/foo/GitRepos/edge-e2e/test-runner/edgehub_factory.py", line 66, in _useExistingHub
    self._finishHubSetup()
  File "/home/foo/GitRepos/edge-e2e/test-runner/edgehub_factory.py", line 70, in _finishHubSetup
    self.edge_hub_device_id
  File "/home/foo/GitRepos/edge-e2e/test-runner/service_helper.py", line 35, in get_device_connection_string
    device = self.service.get_device(device_id, custom_headers=self.headers())
  File "/home/foo/GitRepos/edge-e2e/test-runner/rest_wrappers/generated/service20180630/operations/service_operations.py", line 641, in get_device
    raise HttpOperationError(self._deserialize, response)
msrest.exceptions.HttpOperationError: Operation returned an invalid status code 'Not Found'
deploy_test_containers.py failed

```

**Likely Cause:**

Try examining the iotedge logs by running: 

`sudo systemctl -u iotedge -f`

To view more detailed logs use the following commands:

```
sudo systemctl edit iotedge.service
```

Update the following lines:
```
[Service]
Environment=IOTEDGE_LOG=edgelet=debug
```

Restart IoT Edge Security Daemon:

```
sudo systemctl cat iotedge.service
sudo systemctl daemon-reload
sudo systemctl restart iotedge
```

If you see some error like the following...

```
[WARN] - Could not create module nodeMod
[WARN] -         caused by: No such image: iotfoocontainers.azurecr.io/edge-e2e-node6:latest
```

... then check the environment variables you are using for your container registry. Likely it is not pointing to a valid container registry, or the container image is just not there.

### Test Module not showing up in `iotedge list`

If this is the first time you are running `./create-new-edgehub-device.sh`, or the first time you are deploying a specific image through `deploy-test-containers.sh`, it might take a minute for the containers to download from the container repo. This is a non-obvious hidden time tax. 

If it is still not showing up, try checking the environment variables by running the following in python3 (via terminal shell):

```
import os

print("\n", "IOTHUB Environment Variables:")
for variable in os.environ:
    if "IOTHUB" in variable:
        print(variable, "\n")

```

Be sure you have run `./set-environment.sh` and `./set-ubuntu.sh` if you are running Ubuntu. 

## Selecting a specific version of C SDK from Azure Pipelines for Local Debugging 

Select a reference build for the C SDK on the edge-e2e-c pipeline.

```
https://azure-iot-sdks.visualstudio.com/azure-iot-sdks/_build/results?buildId=8948
```

To get this build running we would then use the tag vsts-8948.

We login to the docker registry so we can pull from the command line -- this way we know we have the container and we don't have to wait for edge to download it (which seems slower than doing it ourselves)

`docker login -u $IOTHUB_E2E_REPO_USER -p $IOTHUB_E2E_REPO_PASSWORD $IOTHUB_E2E_REPO_ADDRESS`

Then we pull the image to get it into our local image cache

`docker pull iotsdke2e.azurecr.io/c-e2e:vsts-8948`

Then, to get it running, we deploy it

`scripts/deploy-test-containers.sh --friend --c iotsdke2e.azurecr.io/c-e2e:vsts-8948`

If that works, `docker ps` or `iotedge list` should show the cMod container existing "since a few secodns ago" or something similar. 



