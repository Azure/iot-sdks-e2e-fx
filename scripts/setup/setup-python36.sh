# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)
root_dir=$(cd ${script_dir}/../.. && pwd)
source "$script_dir/../colorecho.sh"

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

colorecho $_yellow "Installing python libraries"
cd ${root_dir}/ci-wrappers/pythonpreview/wrapper  &&  \
    python3 -m pip install --user -e python_glue
if [ $? -ne 0 ]; then 
    colorecho $_yellow "user path not accepted.  Installing globally"
    cd ${root_dir}/ci-wrappers/pythonpreview/wrapper  &&  \
        python3 -m pip install -e python_glue
    [ $? -eq 0 ] || { colorecho $_red "install python_glue failed"; exit 1; }
fi

cd ${root_dir} &&  \
    python3 -m pip install --user -e horton_helpers
if [ $? -ne 0 ]; then 
    colorecho $_yellow "user path not accepted.  Installing globally"
    cd ${root_dir} &&  \
        python3 -m pip install -e horton_helpers
    [ $? -eq 0 ] || { colorecho $_red "install horton_helpers failed"; exit 1; }
fi

# install requirements for our test runner
cd ${root_dir}/test-runner &&  \
    python3 -m pip install --user -r requirements.txt
if [ $? -ne 0 ]; then 
    colorecho $_yellow "user path not accepted.  Installing globally"
    cd ${root_dir}/test-runner &&  \
        python3 -m pip install -r requirements.txt
    [ $? -eq 0 ] || { colorecho $_red "pip install requirements.txt failed"; exit 1; }
fi

colorecho $_green "Python3 and Python libraries installed successfully"


