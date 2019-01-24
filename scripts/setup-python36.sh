# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# Make sure we're running python 3.5 or higher
needpython=1
which pytho3 > /dev/null
if [ $? -eq 0 ]; then
  ret=`python3 -c 'import sys; print("%i" % (sys.hexversion>0x03050000))'`
  if [ $ret -eq 1 ]; then
    echo "Python3.5+ is already installed"
    needpython=0
  fi
fi

if [ $needpython -eq 1 ]; then
  sudo apt-get install -y python3 python3-pip
  [ $? -eq 0 ] || { echo "apt-get for python3 failed"; exit 1; }
fi


python3 -m pip install --upgrade pip
[ $? -eq 0 ] || { echo "pip upgrade failed"; exit 1; }

# install requirements for our test runner
pushd $(dirname "$0")/../test-runner
[ $? -eq 0 ] || { echo "pushd test-runner failed"; exit 1; }

python3 -m pip install --user -r requirements.txt
[ $? -eq 0 ] || { echo "pip install requirements.txt failed"; exit 1; }

popd

