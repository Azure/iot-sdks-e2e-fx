# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

echo "stopping local registry"
sudo docker stop registry

echo "removing exited containers"
sudo docker rm $(docker ps -a -f status=exited -q)

echo "removing containers that were created but never used"
sudo docker rm $(docker ps -a -f status=created -q)

echo "removing dangling images"
sudo docker rmi $(docker images -q -f dangling=true)

echo "starting registry again"
${script_dir}/setup-registry.sh
[ $? -eq 0 ] || { echo "setup-registry failed"; exit 1; }

