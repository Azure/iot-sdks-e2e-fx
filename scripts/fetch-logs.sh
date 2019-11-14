# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

deployment_type=$1
result_root=$2
job_name=$3

case "$deployment_type" in
  iothub)
    module_list=testMod
    ;;
  iotedge)
    module_list="testMod friendMod edgeHub edgeAgent"
    ;;
  *)
    echo "Usage: $0 [iothub | edgehub] result_root job_name"
    exit 1
    ;;
esac

echo "running docker ps -a"
sudo -n docker ps -a
[ $? -eq 0 ] || { echo "error running docker ps"; exit 1; }

resultsdir=${result_root}/${job_name}
mkdir -p $resultsdir
[ $? -eq 0 ] || { echo "mkdir ${resultsdir} failed"; exit 1; }

pushd $resultsdir
[ $? -eq 0 ] || { echo "pushd ${resultsdir} failed"; exit 1; }

echo "fetching docker logs for ${module_list}"
for mod in ${module_list}; do
  echo "getting log for $mod"
  sudo docker logs -t ${mod} &> ${mod}.log 
  [ $? -eq 0 ] || { echo "error fetching logs for ${mod}"; exit 1; }
done

if [ "${deployment_type}" -eq "iotedge" ]; then
    echo getting iotedged log
    sudo journalctl -u iotedge -n 500 -e  &> iotedged.log
    [ $? -eq 0 ] || { echo "error fetching iotedged journal"; exit 1; }
fi

echo "merging logs"
args="-filterfile ${root_dir}/pyscripts/docker_log_processor_filters.json"
for mod in ${module_list}; do
    args="${args} -staticfile ${mod}.log"
done
python ${root_dir}/pyscripts/docker_log_processor.py $args > merged.log
[ $? -eq 0 ] || { echo "error merging logs"; exit 1; }

echo "saving original junit"
cp "../TEST-${job_name}.xml" "./TEST-${job_name}.orig_xml"
[ $? -eq 0 ] || { echo "error saving junit"; exit 1; }

echo "injecting merged.log into junit"
python ${root_dir}/pyscripts/inject_into_junit.py -junit_file ../TEST-${job_name}.xml -log_file merged.log
[ $? -eq 0 ] || { echo "error injecting into junit"; exit 1; }

