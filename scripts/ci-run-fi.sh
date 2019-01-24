# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)
test_dir=$root_dir/test-runner


transport=$1
shift

language=$1
shift

if [ -z ${transport} ] ||
   [ -z ${language} ]; then
  echo "incorrect parameters."
  echo "Usage: $0 [transport] [language] [args...]"
  echo "e.g. $0 mqtt node --direct-to-iothub"
  exit 1
fi

source ${script_dir}/set-environment.sh
[ $? -eq 0 ] || { echo "set-environment.sh failed"; exit 1; }

pushd $test_dir
[ $? -eq 0 ] || { echo "pushd failed"; exit 1; }

$script_dir/clear-docker-logs.sh
# ignore result

for container in edgeHub friendMod ${language}Mod; do
  $script_dir/restart-docker-container.sh $container
  [ $? -eq 0 ] || { echo "failed to restart $container"; exit 1; }
done

echo "sleeping for 15 seconds for modules to start up"
sleep 15

resultroot=$root_dir/results
junit_suite_name=$language-$transport
junit_filename=$resultroot/TEST-$junit_suite_name.xml
resultdir=$resultroot/$junit_suite_name

mkdir -p $resultdir
[ $? -eq 0 ] || { echo "failed to mkdir $resultdir"; exit 1; }

PYTEST_ARGS="-u -m pytest -v -m "testgroup_edgehub_fault_injection" --transport=$transport --$language-wrapper --junitxml=$junit_filename -o junit_suite_name=$junit_suite_name"

if [ ! "x$STOP_AFTER_FIRST_FAILURE" = "x" ]; then
  echo "STOP_AFTER_FIRST_FAILURE set.  Stopping pytest after first failure."
  PYTEST_ARGS="$PYTEST_ARGS --exitfirst"
fi

echo pytest args are "${PYTEST_ARGS}"

for i in 1 2 3 4 5 6 7 8
do
  echo "Executing Test Number $i"
  python $PYTEST_ARGS $@ |& tee $resultdir/console.log
  if [ ${PIPESTATUS[0]} -ne 0 ]; then
    # $? returns the exit code from tee.  We don't want that.  we want the exit code for pytest, which we can get from ${PIPESTATUS[0]}
    echo "pytest returned failure for $tag $language $transport"
    return_code=1
  else
    echo "pytest returned success for $tag $language $transport"
  fi
  sudo docker restart cMod friendMod edgeHub
done


for mod in ${language}Mod friendMod edgeHub edgeAgent; do
  echo "getting log for $mod"
  sudo docker logs -t ${mod} > $resultdir/${mod}.log 2>&1
done

exit $return_code

