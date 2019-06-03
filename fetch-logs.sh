# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

echo "fetching docker logs"
if [ "$1" != "" ]; then
    languageMod=$1Mod
    echo "including $languageMod"
fi

resultsdir=$root_dir/results/logs
mkdir -p $resultsdir

for mod in ${languageMod} friendMod edgeHub edgeAgent; do
  echo "getting log for $mod"
  sudo docker logs -t ${mod} &> $resultsdir/${mod}.log 
  if [ $? -ne 0 ]; then
    echo "error fetching logs for ${mod}"
  fi
done

sudo journalctl -u iotedge -n 500 -e  &> $resultsdir/iotedged.log
if [ $? -ne 0 ]; then
  echo "error fetching iotedged journal"
fi

args=
for mod in ${languageMod} friendMod edgeHub edgeAgent; do
    args="${args} -staticfile ${mod}.log"
done
pushd $resultsdir && python ${root_dir}/pyscripts/docker_log_processor.py $args > merged.log
if [ $? -ne 0 ]; then
  echo "error merging logs"
fi

echo "injecting merged.log into junit"
pushd $resultsdir && python ${root_dir}/pyscripts/inject_into_junit.py -junit_file $2 -log_file merged.log
if [ $? -ne 0 ]; then
  echo "error injecting into junit"
fi

