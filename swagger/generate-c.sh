# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

echo "WARNING: This script overwrites code.  If you have anything checked out, it might be destroyed by this script."
echo "Do you wish to run this anyway?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

cd ${root_dir}/swagger
[ $? -eq 0 ] || { echo "cd swagger failed"; exit 1; }

rm -r swagger_generated/c
# OK to fail

./generate.sh c
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

echo "cleaning out old wrappers"
cd ${root_dir}/docker_images/c/wrapper/generated
[ $? -eq 0 ] || { echo "cd ${root_dir}/docker-images/c/wrapper/generated failed"; exit 1; }

rm *
[ $? -eq 0 ] || { echo "rm generated/* failed"; exit 1; }

echo "copying generated files"

cp -r ${script_dir}/swagger_generated/c/api/* .
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

# remove trailing whitespace
for f in *; do 
    perl -p -i -e 's/[ \t]+$//' ${f}
    [ $? -eq 0 ] || { echo "perl ${f}"; exit 1; }
done

echo "SUCCESS!"
