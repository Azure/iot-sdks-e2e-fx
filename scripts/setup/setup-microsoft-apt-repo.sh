# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
source "$script_dir/../colorecho.sh"

if [ $(lsb_release -is) != "Ubuntu" ]; then
  colorecho $_red "ERROR: This script only works on Ubunto distros"
  exit 1
fi

colorecho $_yellow "Checking for Microsoft APT repo registration"
if [ -f /etc/apt/sources.list.d/microsoft-prod.list ]; then 
  colorecho $_green "Microsoft APT repa already registered.  Done."
  exit 0
fi

# Download the Microsoft repository GPG keys
wget -q https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/packages-microsoft-prod.deb
[ $? -eq 0 ] || { colorecho $_red "wget failed"; exit 1; }

# Register the Microsoft repository GPG keys
sudo dpkg -i packages-microsoft-prod.deb
[ $? -eq 0 ] || { colorecho $_red "dpkg failed"; exit 1; }

rm packages-microsoft-prod.deb

# Update the list of products
sudo apt-get update
[ $? -eq 0 ] || { colorecho $_red "apt update failed"; exit 1; }

colorecho $_green "Microsoft APT repo successfully registered"

