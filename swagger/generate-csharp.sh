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

rm -r swagger_generated/csharp
# OK to fail

./generate.sh csharp
[ $? -eq 0 ] || { echo "generate.sh failed"; exit 1; }

colorecho $_yellow "cleaning out old wrappers"
cd ${root_dir}/docker_images/csharp/wrapper/src
[ $? -eq 0 ] || { echo "cd ${root_dir}/docker-images/csharp/wrapper/src failed"; exit 1; }

for f in $(find . -type f); do
    if [[ "$f" =~ Glue.cs$ ]] || 
       [[ "$f" =~ \.gitignore$ ]] ||
       [[ "$f" =~ ConsoleEventListener.cs ]] ||
       [[ "$f" =~ edge-e2e.csproj ]] ||
       [[ "$f" =~ edge-e2e.sln ]]; then
        colorecho $_green "skipping $f"
    else
        colorecho $_yellow "removing $f"
        rm $f
    fi
done

colorecho $_yellow "copying generated files"
cp -r ${script_dir}/swagger_generated/csharp/src/IO.Swagger/* .
[ $? -eq 0 ] || { echo "cp failed"; exit 1; }

rm IO.Swagger.csproj
rm Dockerfile

colorecho $_green "SUCCESS!"
