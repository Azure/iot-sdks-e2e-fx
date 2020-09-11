# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /src
[ $? -eq 0 ] || { echo "cd src failed"; exit 1; }

cp sdk/package.json .
[ $? -eq 0 ] || { echo "cp package.json failed"; exit 1; }

npm install
[ $? -eq 0 ] || { echo "npm install failed"; exit 1; }

cp sdk/lerna.json .
[ $? -eq 0 ] || { echo "cp lerna.json failed"; exit 1; }

node /fixLerna.js
[ $? -eq 0 ] || { echo "fixLerna.js failed"; exit 1; }

lerna bootstrap --hoist
[ $? -eq 0 ] || { echo "lerna bootstrap failed"; exit 1; }

