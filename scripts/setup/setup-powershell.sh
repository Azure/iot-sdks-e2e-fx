# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
source "$script_dir/../colorecho.sh"

colorecho $_yellow "Checking for powershell install"
pwsh -v > /dev/null
if [ $? -eq 0 ]; then 
  colorecho $_green "Powershell is already installed.  done"
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

# Enable the "universe" repositories
sudo add-apt-repository universe
[ $? -eq 0 ] || { colorecho $_red "add-apt-repository failed"; exit 1; }

# Install PowerShell
sudo apt-get install -y powershell
[ $? -eq 0 ] || { colorecho $_red "apt install powershell failed"; exit 1; }

colorecho $_green "powershell successfully installed"

