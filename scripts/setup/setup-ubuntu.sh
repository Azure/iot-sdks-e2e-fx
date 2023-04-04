# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

function header {
  echo "----------------------------------------------------------"
  echo $@
  echo "----------------------------------------------------------"
}

function failure {
  header $@
  exit 1
}

header "installing moby"
$script_dir/setup-moby.sh
[ $? -eq 0 ] || failure "setup-moby failed"

header "installing local container registry"
$script_dir/setup-registry.sh
[ $? -eq 0 ] || failure "setup-registry failed"

header "installing iotedge"
$script_dir/setup-iotedge.sh
[ $? -eq 0 ] || failure "setup-iotedge failed"

header "\n\
setup-ubuntu succeeded\n\
\n\
Please open a new bash prompt before continuing\n\
\n\
If you get permission errors from docker, reboot your VM\n\
for group changes to take effect\n\
\n\
"


