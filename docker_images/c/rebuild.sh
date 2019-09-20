# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

mkdir /wrapper/build
cd /wrapper/build 
[ $? -eq 0 ] || { echo "cd build failed "; exit 1; }

if [ -f "CMakeCache.txt" ]; then 
    rm CMakeCache.txt
    echo "removed CMakeCache.txt"
fi

cmake -D BUILD_TESTING=OFF -D use_edge_modules=ON  -D skip_samples=ON C_SDK_ROOT=/sdk -DCMAKE_BUILD_TYPE=Debug -D use_amqp=ON -D use_mqtt=ON -D use_http=ON ..
[ $? -eq 0 ] || { echo "cmake failed"; exit 1; }

make edge_e2e_rest_server
[ $? -eq 0 ] || { echo "make failed"; exit 1; }
