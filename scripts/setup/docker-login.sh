# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
docker login -u $IOTHUB_E2E_REPO_USER -p $IOTHUB_E2E_REPO_PASSWORD $IOTHUB_E2E_REPO_ADDRESS
[ $? -eq 0 ] || { echo "docker login failed"; exit 1; }
