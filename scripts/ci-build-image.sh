# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

python3 ${script_dir}/../pyscripts/build_docker_image.py $@
[ $? -eq 0 ] || { echo "build_docker_image.py failed"; exit 1; }


