# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk
[ $? -eq 0 ] || { echo "cd sdk failed"; exit 1; }

export temp=$1

if [ -s /${temp}/source.tar.gz ]; then 
  mkdir /${temp}/source
  [ $? -eq 0 ] || { echo "mkdir /temp/source failed"; exit 1; }
  tar -zxf /${temp}/source.tar.gz -C /${temp}/source 
  [ $? -eq 0 ] || { echo "tar -zxf failed"; exit 1; }
  if [ -f /etc/alpine-release ]; then
    echo "On alpine - using less efficient rsync opts" 
    rsync --recursive --delete-during  /${temp}/source/ .
    [ $? -eq 0 ] || { echo "rsync failed"; exit 1; }
  else
    rsync --recursive --checksum --update --delete-during  /${temp}/source/ .
    [ $? -eq 0 ] || { echo "rsync failed"; exit 1; }
  fi
else
  git fetch origin 
  [ $? -eq 0 ] || { echo "git fetch failed"; exit 1; }
  git checkout $HORTON_COMMIT_SHA
  [ $? -eq 0 ] || { echo "git checkout failed"; exit 1; }
  git submodule update --init --recursive
  [ $? -eq 0 ] || { echo "git submodule failed"; exit 1; }
fi

