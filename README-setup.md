# Configuring your environment for Edge E2E development

All paths in this document are relative to the edge_e2e directory.

## Step 1: Configure your VM.
I use Ubuntu 18.04.  You can also use Ubuntu 16.04

Reference: https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux.

Reference: https://docs.microsoft.com/en-us/azure/iot-edge/quickstart-linux#install-and-start-the-iot-edge-runtime

1. Create a new VM or use an existing one.
   * Follow this link to [create VM](https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal) directly on the azure portal
   * Use configuration `Standard B2s`

2. Clone https://azure-iot-sdks.visualstudio.com/azure-iot-sdks/_git/edge-e2e
   * This may need a SSH cloning. In that case please generate a ssh key pair and add the value of the public portion key to this repo's manage ssh keys.
3. Set the following environment variables.  I put this into my `~/.bashrc`.

```bash
    export IOTHUB_E2E_REPO_ADDRESS="REDACTED"
    export IOTHUB_E2E_REPO_USER="REDACTED"
    export IOTHUB_E2E_REPO_PASSWORD="REDACTED"

```

4. Run `scripts/setup-ubuntu.sh`.  This will install all software necessary to run iotedge, the containers, and the test runners

## Step 3: Create an edgehub instance in your iothub registry.
5. Set the `IOTHUB_E2E_CONNECTION_STRING` environment variable to the IoTHub instance which you are going to use for your tests. I also put this into my `~/.bashrc`.
   * _This can be the connection string for iothub owner._
6. Run `scripts/create-new-edgehub-device.sh`.  This will create an edge device on your hub, and it will create a "friend device" which will be used for tests that require a device identity.

If this step is successful, you should see your edgeAgent and edgeHub containers created along with friendMod and nodeMod modules.

## Step 4: Run the tests.
`create_new_edgehub_device.py` should have pre-populated your hub with the node.js test module. Now you're going to test against this.

9. If this is your first time running, run `iotedge list` and verify that there's some containers running.  It should have at least edgeAgent, edgeHub, nodeMod and friendMod.
10. In case the list does not show `nodeMod` please run `./scripts/deploy-test-containers.sh  --node --friend` and check again.
11. Run `scripts/ci-run-single-scenario.sh`.
    * The parameters provided for edge-hub are `edgehub`, `mqtt`, `node` and `testgroup_edgehub_module_client`. The command for edge-hub is `scripts/ci-run-single-scenario.sh edgehub mqtt node testgroup_edgehub_module_client`
    * The parameters provided for iot-hub are `iothub`, `mqtt`, `node`, `testgroup_iothub_module_client`, `--direct-to-iothub`. There is an additional parameter in the case of iot-hub.


If this step succeeds: you should see all the tests run and successful results at the bottom.
