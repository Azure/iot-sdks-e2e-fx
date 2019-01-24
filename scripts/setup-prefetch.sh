# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

if [ -z ${IOTHUB_E2E_REPO_USER} ] ||
   [ -z ${IOTHUB_E2E_REPO_PASSWORD} ] ||
   [ -z ${IOTHUB_E2E_REPO_ADDRESS} ]; then
    echo "ERROR: IOTHUB_E2E_REPO* variables are not set."
    echo "Cannot continue.  Exiting"
    exit 1
fi

# fetch our module images.  This makes starting up iotedge later faster.
sudo docker login -u ${IOTHUB_E2E_REPO_USER} -p ${IOTHUB_E2E_REPO_PASSWORD} ${IOTHUB_E2E_REPO_ADDRESS}
[ $? -eq 0 ] || { echo "docker login failed"; exit 1; }

sudo docker pull ${IOTHUB_E2E_REPO_ADDRESS}/edge-e2e-node6
[ $? -eq 0 ] || { echo "docker pull failed"; exit 1; }
