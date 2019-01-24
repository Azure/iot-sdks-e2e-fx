# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

pip install -r ${root_dir}/test-runner/requirements.txt
[ $? -eq 0 ] || { echo "pip install failed"; exit 1; }

if [ -d ${root_dir}/results ]; then
  sudo rm -r ${root_dir}/results
  [ $? -eq 0 ] || { echo "rmdir results failed"; exit 1; }
fi
