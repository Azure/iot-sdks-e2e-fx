# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

${script_dir}/get-environment.sh > /tmp/env.sh
[ $? -eq 0 ] || { echo "get-environment failed"; exit 1; }

source /tmp/env.sh
[ $? -eq 0 ] || { echo "source failed"; exit 1; }

rm /tmp/env.sh
[ $? -eq 0 ] || { echo "rm env.sh failed"; exit 1; }

