# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk
[ $? -eq 0 ] || { echo "cd shared failed"; exit 1; }

npm install
[ $? -eq 0 ] || { echo "npm install failed"; exit 1; }

lerna bootstrap --scope iot-sdk-device-client-rest-api --include-filtered-dependencies --hoist
[ $? -eq 0 ] || { echo "lerna bootstrap failed"; exit 1; }

