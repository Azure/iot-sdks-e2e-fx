# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

echo "Checking for powershell install"
pwsh -v > /dev/null
if [ $? -eq 0 ]; then 
  echo "Powershell is already installed.  done"
  exit 0
fi

# Register the Microsoft repository
$script_dir/setup-microsoft-apt-repo.sh
[ $? -eq 0 ] || { echo "setup-microsoft-apt-repo failed"; exit 1; }

# Enable the "universe" repositories
sudo add-apt-repository universe
[ $? -eq 0 ] || { echo "add-apt-repository failed"; exit 1; }

# Update the list of products
sudo apt-get update
[ $? -eq 0 ] || { echo "apt update failed"; exit 1; }

# Install PowerShell
sudo apt-get install -y powershell
[ $? -eq 0 ] || { echo "apt install powershell failed"; exit 1; }

echo "powershell successfully installed"

