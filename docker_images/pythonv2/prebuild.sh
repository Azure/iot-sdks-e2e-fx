# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

set -e

cd /sdk
pip install --upgrade pip
pip install -U --upgrade-strategy eager -e azure-iot-device --ignore-installed packaging
#pip install -U --upgrade-strategy eager -e azure-iot-hub --ignore-installed packaging
cd /wrapper
pip install -r requirements.txt

