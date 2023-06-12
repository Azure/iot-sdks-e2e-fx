# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd "${script_dir}/.." && pwd)

java_root=$1
if [ ! -f $java_root/iot-e2e-tests/edge-e2e/pom.xml ]; then
    echo "ERROR: File ${java_root}/iot-e2e-tests/edge-e2e/pom.xml does not exist"
    echo usage: $0 [java-root]
    echo e.g.: $0 ~/repos/java
    exit 1
fi

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

rm -r swagger_generated/java
# OK to fail

./generate.sh java
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

echo "cleaning out old wrappers"

cd ${java_root}/iot-e2e-tests/edge-e2e/
[ $? -eq 0 ] || { echo "cd ${java_root}/iot-e2e-tests/edge-e2e/ failed"; exit 1; }

for f in $(find . -type f); do
    if [[ "$f" =~ \/glue\/ ]] ||
       [[ "$f" =~ ApiImpl.java$ ]] ||
       [[ "$f" =~ Main.java$ ]]; then
        echo "skipping $f"
    else
        echo "removing $f"
        rm $f
    fi
done

echo "copying generated files"
cp -r ${script_dir}/swagger_generated/java/* .
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

# remove trailing whitespace
for f in $(find . -type f); do
    perl -p -i -e 's/[ \t]+$//' ${f}
    [ $? -eq 0 ] || { echo "perl ${f}"; exit 1; }
done


echo "SUCCESS!"
