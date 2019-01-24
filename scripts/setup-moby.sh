# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

unset moby_cli_installed
dpkg -s moby-cli | grep -q "install ok installed"
if [ $? -eq 0 ]; then moby_cli_installed=true; fi

unset moby_engine_installed
dpkg -s moby-engine | grep -q "install ok installed"
if [ $? -eq 0 ]; then moby_engine_installed=true; fi

if [ $moby_engine_installed ] && [ $moby_cli_installed ]; then
  echo "moby is already installed"
  exit 0
fi

unset docker_installed
which docker > /dev/null
if [ $? -eq 0 ]; then docker_installed=true; fi

if [ $docker_installed ]; then
  echo "docker is already installed"
  exit 0
fi

if [ $(lsb_release -is) != "Ubuntu" ]; then
  echo "ERROR: This script only works on Ubunto distros"
  exit 1
fi

which curl > /dev/null
if [ $? -ne 0 ]; then
  sudo apt-get install -y curl
fi

# add pointers to the Microsoft APT repository

if [ $(lsb_release -rs) == "16.04" ]; then
  # BEGIN 16.04-specific steps
  # Install repository configuration (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > ./microsoft-prod.list
  [ $? -eq 0 ] || { echo "curl failed"; exit 1; }
  sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
  [ $? -eq 0 ] || { echo "sudo cp failed"; exit 1; }

  rm ./microsoft-prod.list

  # Install Microsoft GPG public key (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
  [ $? -eq 0 ] || { echo "curl failed"; exit 1; }
  sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
  [ $? -eq 0 ] || { echo "sudo cp failed"; exit 1; }

  rm ./microsoft.gpg

  # END 16.04-specific steps
elif [ $(lsb_release -rs) == "18.04" ]; then
  # BEGIN 18.04-specific steps
  # Install repository configuration (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > ./microsoft-prod.list
  [ $? -eq 0 ] || { echo "curl failed"; exit 1; }
  sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
  [ $? -eq 0 ] || { echo "sudo cp failed"; exit 1; }

  rm ./microsoft-prod.list

  # Install Microsoft GPG public key (from https://docs.microsoft.com/en-us/azure/iot-edge/how-to-install-iot-edge-linux)
  curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
  [ $? -eq 0 ] || { echo "curl failed"; exit 1; }
  sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
  [ $? -eq 0 ] || { echo "sudo cp failed"; exit 1; }

  rm ./microsoft.gpg

  # END 18.04-specific steps
else
  echo "ERROR: this script only works with Ubuntu 16.04 and Ubuntu 18.04"
  exit 1
fi

# install docker engine

sudo apt-get update
[ $? -eq 0 ] || { echo "apt-get update failed"; exit 1; }

sudo apt-get install -y moby-engine
[ $? -eq 0 ] || { echo "apt-get failed"; exit 1; }

sudo apt-get install -y moby-cli
[ $? -eq 0 ] || { echo "apt-get failed"; exit 1; }

# wait for the docker engine to start.
sleep 10s

# add a group called 'docker' so we can add ourselves to it.  Sometimes it gets automatically created, sometimes not.
sudo groupadd docker
# allowed to fail if the group already exists

# add ourselves to the docker group.  The user will have to restart the bash prompt to run docker, so we'll just
# sudo all of our docker calls in this script.
sudo usermod -aG docker $USER
[ $? -eq 0 ] || { echo "usermod failed"; exit 1; }
