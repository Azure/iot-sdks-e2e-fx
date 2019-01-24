# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

CONTAINERNAME=$1
if [ -z ${CONTAINERNAME} ]; then
  echo "usage: $0 [containername]"
  exit 1
fi

echo "calling \"docker restart $CONTAINERNAME\""
sudo docker restart $1
[ $? -eq 0 ] || { echo "docker restart failed"; exit 1; }

${script_dir}/wait-for-container.sh $1
[ $? -eq 0 ] || { echo "wait-for-container.sh failed"; exit 1; }

