# readme for e2e test runner


## Environment
When running the scripts in this folder, you need to set the following environment variables:

* `IOTHUB_E2E_CONNECTION_STRING`: Connection string of the iothub that contains your edgehub instance.  This is something you have to create and set manually

Additionally, you temporarily need these variables to get to the container repository.  These are available in our developer keyvault
* `IOTHUB_E2E_REPO_ADDRESS`: Address of the docker container repository that hosts container images.
* `IOTHUB_E2E_REPO_USER`: User name for the docker container repository that hosts container images
* `IOTHUB_E2E_REPO_PASSWORD`: Password for the docker container repository that hosts container images

The following variables can be used to customize your edge containers.  Suggested values are also in our keyvault
* `IOTHUB_E2E_EDGE_PRIVATE_REGISTRY`: JSON for extra container registry credentials
* `IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE`: image name to use for overriding default edgeAgent image
* `IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE`: image name to use for overriding default edgeHub image

If you are running the tests remotely (outside of your IotEdge device), you will also need to set the following variables:
* `IOTHUB_E2E_EDGEHUB_DNS_NAME`: The DNS name or IP address of the VM that's hosting the edgehub executable.  This is the network name or IP address of the VM that's running the edgeHub service
* `IOTHUB_E2E_EDGEHUB_DEVICE_ID`: Device ID of your edgehub instance.
* `IOTHUB_E2E_EDGEHUB_CA_CERT`: CA certificate for your edgehub service, base64 encoded.

If you want to make an easy copy of these variables for running remotely, you can run `scripts/get-environment.sh windows`