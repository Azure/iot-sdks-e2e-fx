# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk
[ $? -eq 0 ] || { echo "cd sdk failed"; exit 1; }

export temp=$1

if [ -s /${temp}/source.tar.gz ]; then 
  mkdir /${temp}/source && 
  tar -zxf /${temp}/source.tar.gz -C /${temp}/source 
  rsync --recursive --checksum --update /${temp}/source/ . 
else
  git fetch origin 
  git checkout $HORTON_COMMIT_SHA
  git submodule update --init --recursive
fi

