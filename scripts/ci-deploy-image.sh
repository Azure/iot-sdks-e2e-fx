# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)
test_dir=$root_dir/test-runner

source ${script_dir}/_ci-parse-parameters.sh $@
[ $? -eq 0 ] || { echo "_ci-parse-parameters.sh failed"; exit 1; }

cd ${script_dir}/../pyscripts
[ $? -eq 0 ] || { echo "cd ${script_dir}/../pyscripts failed"; exit 1; }

export DOCKER_FULLNAME="localhost:5000/${LANGUAGE}-e2e:latest"
echo "running with $DOCKER_FULLNAME"

cd ${script_dir}
[ $? -eq 0 ] || { echo "cd ${script_dir} failed"; exit 1; }

python3 ${root_dir}/pyscripts/deploy_test_containers.py --friend --${LANGUAGE} ${DOCKER_FULLNAME}
[ $? -eq 0 ] || { echo "python3 deployment script failed"; exit 1; }

${script_dir}/force-restart-iotedge-clean.sh friend ${language}
[ $? -eq 0 ] || { echo "edgehub restart failed"; exit 1; }

$script_dir/verify-deployment.sh ${LANGUAGE}Mod ${DOCKER_FULLNAME}
[ $? -eq 0 ] || { echo "deployment verification failed"; exit 1; }





