# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

if [ ! -f sdk/lerna.json ]; then
    if [ ! -f $1/lerna.json ]; then
        echo "usage: $0 <node_root>"
        echo "e.g.: $0 ~/repos/node"
        exit 1
    fi

    ln -s $1 sdk
    [ $? -eq 0 ] || { echo "ln -s $1 sdk failed"; exit 1; }
fi

cp sdk/package.json .
[ $? -eq 0 ] || { echo "cp package.json failed"; exit 1; }

npm install
[ $? -eq 0 ] || { echo "npm install failed"; exit 1; }

cp sdk/lerna.json .
[ $? -eq 0 ] || { echo "cp lerna.json failed"; exit 1; }

node fixLerna.js
[ $? -eq 0 ] || { echo "fixLerna.js failed"; exit 1; }

lerna bootstrap --scope iot-sdk-device-client-rest-api --include-filtered-dependencies --hoist
[ $? -eq 0 ] || { echo "lerna bootstrap failed"; exit 1; }

lerna run build --scope iot-sdk-device-client-rest-api --include-filtered-dependencies
[ $? -eq 0 ] || { echo "lerna run build failed"; exit 1; }

