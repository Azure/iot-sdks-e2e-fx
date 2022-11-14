# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

$script_dir/setup-microsoft-apt-repo.sh
[ $? -eq 0 ] || { echo "setup-microsoft-apt-repo failed"; exit 1; }

# install iotedge
sudo apt-get install -y aziot-edge
[ $? -eq 0 ] || { echo "apt-get install aziot-edge failed"; exit 1; }


