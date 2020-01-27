# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd ${script_dir}/../.. && pwd)
source "$script_dir/../colorecho.sh"

if [ -e ${root_dir}/virtualenv/horton/bin/activate ]; then
    source ${root_dir}/virtualenv/horton/bin/activate
    [ $? -eq 0 ] || { colorecho $_red "horton/bin/activate failed"; exit 1; }

    exit 0
fi

colorecho $_yellow "Initializing horton environment"

# Make sure we're running python 3.5 or higher
colorecho $_yellow "checking for python 3.5+"
needpython=1
which python3 > /dev/null
if [ $? -eq 0 ]; then
  ret=`python3 -c 'import sys; print("%i" % (sys.hexversion>0x03050000))'`
  if [ $ret -eq 1 ]; then
    colorecho $_yellow "Python3.5+ is already installed"
    needpython=0
  fi
fi

if [ $needpython -eq 1 ]; then
  colorecho $_yellow "Installing python3"
  sudo apt-get install -y python3
  [ $? -eq 0 ] || { colorecho $_red "apt-get for python3 failed"; exit 1; }
fi

colorecho $_yellow "Checking for pip3"
which pip3 > /dev/null
if [ $? -ne 0 ]; then
    colorecho $_yellow "installing pip3"
    sudo apt-get install -y python3-pip
  [ $? -eq 0 ] || { colorecho $_red "apt-get for python3-pip3 failed"; exit 1; }
fi

colorecho $_yellow "Installing virtualenv python libraries"
python3 -m pip install --user virtualenv
if [ $? -ne 0 ]; then 
    colorecho $_yellow "user path not accepted.  Installing globally"
    python3 -m pip install virtualenv
    [ $? -eq 0 ] || { colorecho $_red "pip install requirements.txt failed"; exit 1; }
fi

colorecho $_yellow "Creating virtual evnronment"
python3 -m virtualenv ${root_dir}/virtualenv/horton/
[ $? -eq 0 ] || { colorecho $_red "virtualenv create failed"; exit 1; }

source ${root_dir}/virtualenv/horton/bin/activate
[ $? -eq 0 ] || { colorecho $_red "horton/bin/activate failed"; exit 1; }

colorecho $_green "Horton environment crated"


