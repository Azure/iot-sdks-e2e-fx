# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)
source "$script_dir/../colorecho.sh"

colorecho $_yellow "Checking for moby install"
unset moby_cli_installed
dpkg -s moby-cli | grep -q "install ok installed"
if [ $? -eq 0 ]; then moby_cli_installed=true; fi

unset moby_engine_installed
dpkg -s moby-engine | grep -q "install ok installed"
if [ $? -eq 0 ]; then moby_engine_installed=true; fi

need_moby=true
if [ $moby_engine_installed ] && [ $moby_cli_installed ]; then
  colorecho $_yellow "moby is already installed"
  unset need_moby 
fi

if [ "$need_moby" ]; then 
  colorecho $_yellow "checking for docker install"
  which docker > /dev/null
  if [ $? -eq 0 ]; then
    colorecho $_yellow "docker is already installed"
    unset need_moby
  fi
fi

if [ "$need_moby" ]; then 
  if [ $(lsb_release -is) != "Ubuntu" ]; then
    colorecho $_red "ERROR: This script only works on Ubunto distros"
    exit 1
  fi

  which curl > /dev/null
  if [ $? -ne 0 ]; then
    colorecho $_yellow "installing curl"
    sudo apt-get install -y curl
  fi

  # add pointers to the Microsoft APT repository

  colorecho $_yellow "configuring Microsoft APT repository"
  # Install repository configuration (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > ./microsoft-prod.list
  [ $? -eq 0 ] || { colorecho $_red "curl failed"; exit 1; }
  sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
  [ $? -eq 0 ] || { colorecho $_red "sudo cp failed"; exit 1; }

  rm ./microsoft-prod.list

  # Install Microsoft GPG public key (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
  [ $? -eq 0 ] || { colorecho $_red "curl failed"; exit 1; }
  sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
  [ $? -eq 0 ] || { colorecho $_red "sudo cp failed"; exit 1; }

  rm ./microsoft.gpg

  # install docker engine

  colorecho $_yellow "updating APT cache"
  sudo apt-get update
  [ $? -eq 0 ] || { colorecho $_red "apt-get update failed"; exit 1; }

  colorecho $_yellow "installing moby"
  sudo apt-get install -y moby-engine
  [ $? -eq 0 ] || { colorecho $_red "apt-get failed"; exit 1; }

  sudo apt-get install -y moby-cli
  [ $? -eq 0 ] || { colorecho $_red "apt-get failed"; exit 1; }

  # wait for the docker engine to start.
  sleep 10s
fi

# add a group called 'docker' so we can add ourselves to it.  Sometimes it gets automatically created, sometimes not.
colorecho $_yellow "creating docker group"
sudo groupadd docker
# allowed to fail if the group already exists

# add ourselves to the docker group.  The user will have to restart the bash prompt to run docker, so we'll just
# sudo all of our docker calls in this script.
colorecho $_yellow "adding $USER to docker group"
sudo usermod -aG docker $USER
[ $? -eq 0 ] || { colorecho $_yellow "usermod failed"; exit 1; }

colorecho $_green "Moby/Docker successfully installed"

