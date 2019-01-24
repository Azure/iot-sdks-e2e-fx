#!/bin/bash
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

cd /sdk
[ $? -eq 0 ] || { echo "cd /sdk failed"; exit 1; }

./c/build_all/linux/build.sh --build-python 3.6 --use-edge-modules --no-make
[ $? -eq 0 ] || { echo "build.sh failed"; exit 1; }

${script_dir}/rebuild.sh
[ $? -eq 0 ] || { echo "rebuild.sh failed"; exit 1; }


