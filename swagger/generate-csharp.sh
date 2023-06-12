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

rm -r swagger_generated/csharp
# OK to fail

./generate.sh csharp
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

echo "cleaning out old wrappers"
cd ${root_dir}/docker_images/csharp/wrapper/src
[ $? -eq 0 ] || { echo "cd ${root_dir}/docker-images/csharp/wrapper/src failed"; exit 1; }

for f in $(find . -type f); do
    if [[ "$f" =~ Glue.cs$ ]] || 
       [[ "$f" =~ \.gitignore$ ]] ||
       [[ "$f" =~ ConsoleEventListener.cs ]] ||
       [[ "$f" =~ edge-e2e.csproj ]] ||
       [[ "$f" =~ edge-e2e.sln ]]; then
        echo "skipping $f"
    else
        echo "removing $f"
        rm $f
    fi
done

echo "copying generated files"
cp -r ${script_dir}/swagger_generated/csharp/src/IO.Swagger/* .
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

rm IO.Swagger.csproj
rm Dockerfile

cd Controllers
[ $? -eq 0 ] || { echo "cd Controllers failed"; exit 1; }

# remove trailing whitespace
for f in *; do
    perl -p -i -e 's/[ \t]+$//' ${f}
    [ $? -eq 0 ] || { echo "perl ${f}"; exit 1; }
done


echo "SUCCESS!"
