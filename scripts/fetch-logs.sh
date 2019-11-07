# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

echo "fetching docker logs"

resultsdir=$root_dir/results/$1
mkdir -p $resultsdir

for mod in testMod friendMod edgeHub edgeAgent; do
  echo "getting log for $mod"
  sudo docker logs -t ${mod} &> $resultsdir/${mod}.log 
  if [ $? -ne 0 ]; then
    echo "error fetching logs for ${mod}"
    exit 1
  fi
done

sudo journalctl -u iotedge -n 500 -e  &> $resultsdir/iotedged.log
if [ $? -ne 0 ]; then
  echo "error fetching iotedged journal"
  exit 1
fi

args="-filterfile ${root_dir}/pyscripts/docker_log_processor_filters.json"
for mod in testMod friendMod edgeHub edgeAgent; do
    args="${args} -staticfile ${mod}.log"
done
pushd $resultsdir && python ${root_dir}/pyscripts/docker_log_processor.py $args > merged.log
if [ $? -ne 0 ]; then
  echo "error merging logs"
  exit 1
fi

echo "injecting merged.log into junit"
pushd $resultsdir && python ${root_dir}/pyscripts/inject_into_junit.py -junit_file ../TEST-$1.xml -log_file merged.log
if [ $? -ne 0 ]; then
  echo "error injecting into junit"
  exit 1
fi

