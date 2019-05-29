# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

source "$script_dir/../colorecho.sh"

function header {
  color="$1"
  shift
  colorecho $color "----------------------------------------------------------"
  colorecho $color $@
  colorecho $color "----------------------------------------------------------"
}

function failure {
  header $_green $@
  exit 1
}

header $_cyan "installing python 3.6"
$script_dir/setup-python36.sh
[ $? -eq 0 ] ||  failure "setup-python36 failed"

header $_cyan "installing moby"
$script_dir/setup-moby.sh
[ $? -eq 0 ] || failure "setup-moby failed"

header $_cyan "installing local container registry"
$script_dir/setup-registry.sh
[ $? -eq 0 ] || failure "setup-registry failed"

header $_cyan "installing iotedge"
$script_dir/setup-iotedge.sh
[ $? -eq 0 ] || failure "setup-iotedge failed"

header $_green "\n\
setup-ubuntu succeeded\n\
\n\
Please open a new bash prompt before continuing\n\
\n\
If you get permission errors from docker, reboot your VM\n\
for group changes to take effect\n\
\n\
"


