# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
source "$script_dir/../colorecho.sh"
source /etc/os-release


colorecho $_yellow "Checking for Microsoft APT repo registration"
if [ -f /etc/apt/sources.list.d/microsoft-prod.list ]; then 
  colorecho $_green "Microsoft APT repo already registered.  Done."
  exit 0
fi

# Download the Microsoft repository GPG keys
case $ID in
    linuxmint)
        if [[ $VERSION_ID == "19.3" ]];
        then
            os_platform="ubuntu/18.04/multiarch"
        fi
        ;;
    ubuntu)
        if [[ $VERSION_ID == "18.04" ]];
        then
            os_platform="$ID/$VERSION_ID/multiarch"
        else
            os_platform="$ID/$VERSION_ID"
        fi
        ;;

    raspbian)
        if [ "$VERSION_CODENAME" == "bullseye" ] || [ "$VERSION_ID" == "11" ];
        then
            os_platform="$ID_LIKE/11"               
        else
            os_platform="$ID_LIKE/stretch/multiarch"
        fi
        ;;
esac

if [ "${os_platform}" == "" ]; then
  colorecho $_red "ERROR: This script only works on Ubunto and Raspbian distros"
  exit 1
fi

curl https://packages.microsoft.com/config/${os_platform}/prod.list > ./microsoft-prod.list
[ $? -eq 0 ] || { colorecho $_red "curl failed"; exit 1; }

# Register the Microsoft repository GPG keys
sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
[ $? -eq 0 ] || { colorecho $_red "sudo cp microsoft-prod.list failed"; exit 1; }

rm microsoft-prod.list

curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
[ $? -eq 0 ] || { colorecho $_red "curl microsoft.asc failed"; exit 1; }

sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
[ $? -eq 0 ] || { colorecho $_red "cp microsoft.gpg failed"; exit 1; }

rm microsoft.gpg

# Update the list of products
sudo apt-get update
[ $? -eq 0 ] || { colorecho $_red "apt update failed"; exit 1; }

colorecho $_green "Microsoft APT repo successfully registered"

