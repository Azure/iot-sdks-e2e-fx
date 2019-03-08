# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)
test_dir=$root_dir/test-runner

language=$1
case "$language" in
  node | python | c | csharp | java | pythonpreview)
    echo "running tests for for $language"
    ;;
  *)
    echo "Usage: $0 [node | python | c | csharp | java | pythonpreview]"
    exit 1
    ;;
esac

return_code=0
return_string=""

function end_script {
  echo ""
  echo "FINAL RESULTS:"
  echo ""
  echo "$return_string"
  exit $return_code
}

function run_single_scenario {
  tag=$1
  shift
  transport=$1
  shift
  language=$1
  shift
  scenario=$1
  shift
  $script_dir/ci-run-single-scenario.sh $tag $transport $language $scenario $@
  if [ $? -ne 0 ]; then
    return_code=1
    return_string="$return_string"$'\n'"FAILED: $tag $transport $language"
    if [ ! "x$STOP_AFTER_FIRST_FAILURE" = "x" ]; then
      echo "STOP_AFTER_FIRST_FAILURE set.  Stopping test."
      end_script
    fi
  else
    return_string="$return_string"$'\n'"SUCCEEDED: $tag $transport $language"
  fi
}

for transport in amqp amqpws mqtt mqttws ; do
  echo "---------------------------------------------------------------------------"
  echo "running edgehub $transport $language"
  echo "---------------------------------------------------------------------------"
  if [ "$transport" = "amqp" ] || [ "$transport" = "amqpws" ]; then
    if [ "$language" = "c" ] || [ "$language" = "python" ]; then
      echo "transport $transport is not supported by $language for edgehub.  skipping."
      continue
    fi
  fi
  if [ "$language" = "pythonpreview" ]; then
    if [ ! "$transport" = "mqtt" ]; then
      echo "transport $transport is not supported by $language for edgehub.  skipping."
      continue
    fi
  fi
  run_single_scenario edgehub $transport $language edgehub_module
done

for transport in amqp amqpws mqtt mqttws; do
  echo "---------------------------------------------------------------------------"
  echo "running iothub $transport $language"
  echo "---------------------------------------------------------------------------"
  if [ "$language" = "pythonpreview" ]; then
    if [ ! "$transport" = "mqtt" ]; then
      echo "transport $transport is not supported by $language for iothub.  skipping."
      continue
    fi
  fi
  run_single_scenario iothub $transport $language iothub_module
done

end_script
