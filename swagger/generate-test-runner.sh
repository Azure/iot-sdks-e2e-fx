# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)
source "$script_dir/../scripts/colorecho.sh"

colorecho $_red "WARNING: This script overwrites code.  If you have anything checked out, it might be destroyed by this script."
colorecho $_red "Do you wish to run this anyway?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

cd ${root_dir}/swagger
[ $? -eq 0 ] || { echo "cd swagger failed"; exit 1; }

rm -r swagger_generated/yaml
# OK to fail

./generate.sh yaml
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

cd swagger_generated/yaml
[ $? -eq 0 ] || { echo "cd swagger_generated/yaml failed"; exit 1; }

mv swagger.yaml e2e-restapi.yaml
[ $? -eq 0 ] || { echo "mv failed"; exit 1; }

autorest --python --input-file=e2e-restapi.yaml
[ $? -eq 0 ] || { echo "autorest failed"; exit 1; }

colorecho $_yellow "copying generated files"

cd ${root_dir}/test-runner/adapters/rest/generated/
[ $? -eq 0 ] || { echo "cd test-runner/rest_wrappers/generated"; exit 1; }

rm -r e2erestapi/
[ $? -eq 0 ] || { echo "rm e2erestapi failed"; exit 1; }

cp -r ../../../swagger/swagger_generated/yaml/generated/e2erestapi/ .
[ $? -eq 0 ] || { echo "cp"; exit 1; }

colorecho $_green "SUCCESS!"
