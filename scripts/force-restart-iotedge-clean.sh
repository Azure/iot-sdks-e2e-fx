# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

echo "stopping iotedge service"
sudo systemctl stop iotedge
[ $? -eq 0 ] || { echo "systemctl stop iotedge failed"; }

modulesToRemove="edgeAgent edgeHub friendMod nodeMod cMod csharpMod javaMod pythonMod pythonpreviewMod"
# modulesToRemove="edgeAgent edgeHub"
for module in $modulesToRemove; do
  sudo docker inspect $module --format="{{.State.Status}}"
  if [ $? -eq 0 ]; then
    echo "stopping $module"
    sudo docker stop $module
    [ $? -eq 0 ] || { echo "docker stop $module failed"; }

    echo "removing $module"
    sudo docker rm $module
    [ $? -eq 0 ] || { echo "docker rm $module failed"; exit 1; }
  fi
done

echo "restarting iotedge service"
sudo systemctl start iotedge
[ $? -eq 0 ] || { echo "systemctl start iotedge failed"; exit 1; }

${script_dir}/wait-for-container.sh edgeAgent
[ $? -eq 0 ] || { echo "edgeAgent failed to start on time"; exit 1; }

${script_dir}/wait-for-container.sh edgeHub
[ $? -eq 0 ] || { echo "edgeHub failed to start on time"; exit 1; }

if [ $# -gt 0 ]; then
  for container in $@; do
    ${script_dir}/wait-for-container.sh ${container}Mod
    [ $? -eq 0 ] || { echo "$container failed to start on time"; exit 1; }
  done
fi
