# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
script_dir=$(cd "$(dirname "$0")" && pwd)

c_root=$1
if [ ! -f ${c_root}/CMakeLists.txt ]; then
    echo "ERROR: File ${c_root}/CMakeLists.txt does not exist"
    echo usage: $0 [c-root]
    echo e.g.: $0 ~/repos/c
    exit 1
fi

# -------------------------------------------------------------
# Make a clone of the restbed repo
sudo rm -r ${script_dir}/wrapper/deps/restbed
# OK to fail.  It might not exist.

mkdir ${script_dir}/wrapper/deps/restbed
[ $? -eq 0 ] || { echo "mkdir restbed failed"; exit 1; }

cd ${script_dir}/wrapper/deps/restbed
[ $? -eq 0 ] || { echo "cd restbed failed"; exit 1; }

git clone https://github.com/Corvusoft/restbed .
[ $? -eq 0 ] || { echo "clone restbed failed"; exit 1; }

git checkout 1b43b9a
[ $? -eq 0 ] || { echo "git checkout failed"; exit 1; }

git submodule update --init --recursive
[ $? -eq 0 ] || { echo "git submodule update failed"; exit 1; }


# -------------------------------------------------------------
# pull the tests out of the CMakeLists file
sed -i '/{PROJECT_SOURCE_DIR}\/test\//d' CMakeLists.txt
[ $? -eq 0 ] || { echo "sed failed"; exit 1; }

# -------------------------------------------------------------
# Build

rm -r ${script_dir}/wrapper/build
# OK to fail.  It might not exist.

mkdir ${script_dir}/wrapper/build
[ $? -eq 0 ] || { echo "mkdir ${script_dir}/wrapper/build failed"; exit 1; }

cd ${script_dir}/wrapper/build
[ $? -eq 0 ] || { echo "cd ${script_dir}/wrapper/build failed"; exit 1; }

cmake -D BUILD_TESTING=OFF -D use_edge_modules=ON  -D skip_samples=ON -D C_SDK_ROOT=${c_root} -DCMAKE_BUILD_TYPE=Debug -D use_amqp=ON -D use_mqtt=ON -D use_http=ON ..
[ $? -eq 0 ] || { echo "cmake failed"; exit 1; }

make edge_e2e_rest_server -j 4
[ $? -eq 0 ] || { echo "make failed"; exit 1; }

echo SUCCESS
echo To build, run 'make edge_e2e_rest_server' in $(pwd)
