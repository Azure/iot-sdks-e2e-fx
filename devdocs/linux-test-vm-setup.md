# Setting up a VM for running tests under Linux

All paths in this document are relative to the iot-sdks-e2e-fx directory.

## Step 1: Decide where do you want to run tests

All of the functionality in this repro should be able to run on any VM.  This means you should be able to spin up an Azure VM, clone this repo, do a little manual setup, and start running tests.  If, however, you need to do any remote debugging involving your desktop PC (e.g. using Visual Studio to debug a C# container), then you will want to use a VM under Hyper-V on your desktop.

All of the instructions for this framework assume you're running commands directly from bash.  It is possible to use GUI tools for some parts (e.g. you can use PyCharm to debug test scripts if you're so inclined), but you're mostly on your own.

## Step 2 (option #1): If using an Azure VM, create the VM
Follow this link to [create VM](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal) directly on the azure portal

Recommended minimum configuration: `Standard B2s`

Recommend image: [Ubuntu Server 18.04 LTS](https://ms.portal.azure.com/#create/Canonical.UbuntuServer1804LTS-ARM)

Recommend region: `South Central US` (primarily for proximity to the private Docker container repository that we use)

## Step 2 (option #2): If you're using Hyper-V on your desktop, configure Hyper-V

When you create your VM under Hyper-V, make sure your VM is connected to a Virtual Switch with `Connection type` set to `External network`.  For instructions, on how to do this, look [here](https://docs.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/create-a-virtual-switch-for-hyper-v-virtual-machines).

If you use the `Hyper-V Quick Create` app to create your VM, you should be aware that the size of the virutal disk on your VM may be limited to a small number (4 GB), which is not enough to run this framework.  You should be prepared to expand your VM storage, or you should create a VM and install Linux manually.

By default, Hyper-V creates VMs with a single virtual CPU.  You should increase this number.  While you're in the settings page, you should also increase the available memory (4 GB+ recommended).

Make sure your virtual disk is big enough.  Because this framework relies heavily on Docker and a local image repository, 100 GB+ is a good size.

[Desktop Ubuntu 18.04](https://www.ubuntu.com/download/desktop/thank-you?country=US&version=18.04.2&architecture=amd64) is recommended.  This framework also been tested on Ubuntu 16.04

## Step 3: Clone this repo and configure your .bashrc

```
bertk@bertk-test-vm:~$ mkdir -p ~/repos/e2e-fx
bertk@bertk-test-vm:~$ cd ~/repos/e2e-fx
bertk@bertk-test-vm:~/repos/e2e-fx$ git clone https://github.com/Azure/iot-sdks-e2e-fx .
Cloning into '.'...
remote: Enumerating objects: 102, done.
remote: Counting objects: 100% (102/102), done.
remote: Compressing objects: 100% (71/71), done.
remote: Total 1093 (delta 48), reused 63 (delta 31), pack-reused 991
Receiving objects: 100% (1093/1093), 1.34 MiB | 8.39 MiB/s, done.
Resolving deltas: 100% (634/634), done.
bertk@bertk-test-vm:~$
```

Now, edit your .bashrc and add the following lines to the end:
```
export IOTHUB_E2E_CONNECTION_STRING="HostName=<REDACTED>;SharedAccessKeyName=<REDACTED>;SharedAccessKey=<REDACTED>"
export IOTHUB_E2E_REPO_USER="<REDACTED>"
export IOTHUB_E2E_REPO_PASSWORD="<REDACTED>"
export IOTHUB_E2E_REPO_ADDRESS="<REDACTED>"
```

__IMPORTANT: replace the \<REDACTED\> values with actual values__

* `IOTHUB_E2E_CONNECTION_STRING` should be the *IoTHub* connection string for a hub that you are using to test (all other resources are created dynamically).  You should use a `SharedAccessKeyName` of `iothubowner` or some other policy that has permissions for `registry write`, `service connect`, and `device connect`
* `IOTHUB_E2E_REPO_USER`, `IOTHUB_E2E_REPO_PASSWORD`, and `IOTHUB_E2E_REPO_ADDRESS` should be retrieved as secrets from the kevault called `sdkbld`

After editing .bashrc, restart your bash session

## Step 4: Use `setup-ubuntu.sh` to install pre-requisites for running tests

```
bertk@bertk-test-vm:~$ cd repos/e2e-fx/
bertk@bertk-test-vm:~/repos/e2e-fx$ scripts/setup-ubuntu.sh
----------------------------------------------------------
installing python 3.6
----------------------------------------------------------

<<snip>>

----------------------------------------------------------

setup-ubuntu succeeded

Please open a new bash prompt before continuing

----------------------------------------------------------
bertk@bertk-test-vm:~/repos/e2e-fx$
```

Next, verify that docker is running:
```
bertk@bertk-test-vm:~$ docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS                    NAMES
d7313d09359f        registry:2          "/entrypoint.sh /etc…"   56 seconds ago      Up 51 seconds       0.0.0.0:5000->5000/tcp   registry
```

**IMPORTANT: `setup_ubuntu.sh` installs the `Moby` engine if the `docker` executable is not found.  Do not attempt to install `Moby` and `Docker` side-by-side.  This will cause configuration problems that are difficult to undo.  For the purposes of this framework, `Moby` and `Docker` are synonymous**

## What have you accomplished and why is it important?

After you're done with this, you have a VM that should be pre-configured to run tests using the Horton framework.  All of the framework tools are installed on your machine at this point.

Up until this point, you haven't made any decisions on what you want to test, and you haven't installed any language-specific or scenario-specific bits.  That comes next.

## What won't we be able to do with this VM?

The scripts available on the VM will allow you to run individual test suites (e.g. "run all IoTEdge module tests _with MQTT_ on the Node.js sdk").  It won't run the Azure pipeline scripts that run multiple suties.  (e.g. "run all IotEdge module tests _with all transports_ on the Node.js sdk).  If you want to run a series of suites, you'll have to script that yourself (keeping in mind that your script will run the suites serially while the Azure DevOps pipelines will run the suites in parallel).

## Where to go next.

After this, you should [run a simple test to verify your installation](./running_your_first_test_suite.md)

