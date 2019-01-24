#!/bin/bash
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk/c/cmake/iotsdk_linux
[ $? -eq 0 ] || { echo "cd iotsdk_linux failed"; exit 1; }

cmake -DCMAKE_BUILD_TYPE=Debug  .
[ $? -eq 0 ] || { echo "cmake failed"; exit 1; }

MAKE_CORES=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || sysctl -n hw.ncpu)
make --jobs=$MAKE_CORES
[ $? -eq 0 ] || { echo "make failed"; exit 1; }

if [ -d /wrapper/swagger_server ]; then
  cd /wrapper/swagger_server
  [ $? -eq 0 ] || { echo "cd swagger_server failed"; exit 1; }

  cp /sdk/c/cmake/iotsdk_linux/python/src/iothub_client.so .
  [ $? -eq 0 ] || { echo "cp client failed"; exit 1; }

  cp /sdk/c/cmake/iotsdk_linux/python_service_client/src/iothub_service_client.so .
  [ $? -eq 0 ] || { echo "cp service_client failed"; exit 1; }
fi
