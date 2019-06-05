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

rm -r swagger_generated/pythonpreview
# OK to fail

./generate.sh pythonpreview
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

colorecho $_yellow "copying generated files"

cd ${root_dir}
[ $? -eq 0 ] || { echo "cd ${root_dir} failed"; exit 1; }

rm -r ci-wrappers/pythonpreview/wrapper/swagger_server
[ $? -eq 0 ] || { echo "rm swagger_swerver failed"; exit 1; }

cp -r swagger/swagger_generated/pythonpreview/swagger_server/ ci-wrappers/pythonpreview/wrapper/swagger_server/
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

rm -r ci-wrappers/pythonpreview/wrapper/swagger_server/test/
[ $? -eq 0 ] || { echo "rm test failed"; exit 1; }

colorecho $_green "SUCCESS!"
