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

rm -r swagger_generated/node
# OK to fail

./generate.sh node
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

echo "cleaning out old wrappers"
cd ${root_dir}/docker_images/node/wrapper/
[ $? -eq 0 ] || { echo "cd ${root_dir}/docker-images/node/wrapper/ failed"; exit 1; }

for f in *; do
    if [ "$f" != "glue" ] && [ "$f" != "node_modules" ]; then
        if [ -d $f ]; then
            echo "--removing directory $f"
            rm -r $f
            [ $? -eq 0 ] || { echo "rm -r $f failed"; exit 1; }
        else
            echo "--removing file $f"
            rm $f
            [ $? -eq 0 ] || { echo "rm $f failed"; exit 1; }
        fi
    fi
done

echo "copying generated files"
cp -r ${script_dir}/swagger_generated/node/* .
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

echo "SUCCESS!"
