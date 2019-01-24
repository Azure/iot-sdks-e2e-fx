# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

# Make sure these variables are set.  We'll need these later when we call fetch_module_images.sh
if [ -z ${IOTHUB_E2E_CONNECTION_STRING} ] ||
   [ -z ${IOTHUB_E2E_REPO_USER} ] ||
   [ -z ${IOTHUB_E2E_REPO_PASSWORD} ] ||
   [ -z ${IOTHUB_E2E_REPO_ADDRESS} ]; then
    echo "ERROR: required env variables are not set."
    echo "Cannot continue.  Exiting"
    exit 1
fi

source ${script_dir}/set-environment.sh
[ $? -eq 0 ] || { echo "set-environment.sh failed"; exit 1; }

source ${script_dir}/_ci-parse-parameters.sh $@
[ $? -eq 0 ] || { echo "_ci-parse-parameters .sh failed"; exit 1; }

${script_dir}/ci-build-image.sh $@
[ $? -eq 0 ] || { echo "ci-build-image.sh failed"; exit 1; }

${script_dir}/ci-deploy-image.sh $@
[ $? -eq 0 ] || { echo "ci-deploy-image.sh failed"; exit 1; }

${script_dir}/ci-run-all-scenarios.sh $LANGUAGE
[ $? -eq 0 ] || { echo "ci-run-all-scenarios.sh failed"; exit 1; }


