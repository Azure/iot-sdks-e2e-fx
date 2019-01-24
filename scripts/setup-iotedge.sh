# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

# install iotedge
sudo apt-get install -y iotedge
[ $? -eq 0 ] || { echo "apt-get install iotedge failed"; exit 1; }

sudo chmod 666 /etc/iotedge/config.yaml
[ $? -eq 0 ] || { echo "sudo chmod"; exit 1; }

