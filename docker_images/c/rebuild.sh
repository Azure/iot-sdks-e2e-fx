# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# Create compatibility symlink for macro-utils-c header path migration
# (new repo uses inc/macro_utils/ but SDK headers still reference azure_macro_utils/)
if [ -d "/sdk/deps/azure-macro-utils-c/inc/macro_utils" ] && [ ! -e "/sdk/deps/azure-macro-utils-c/inc/azure_macro_utils" ]; then
    ln -s macro_utils /sdk/deps/azure-macro-utils-c/inc/azure_macro_utils
fi

mkdir /wrapper/build
cd /wrapper/build 
[ $? -eq 0 ] || { echo "cd build failed "; exit 1; }

if [ -f "CMakeCache.txt" ]; then 
    rm CMakeCache.txt
    echo "removed CMakeCache.txt"
fi

# Drop macro-utils forwarding headers left in the build tree by prebuild.sh.
#
# prebuild.sh builds the default branch of the SDK. When that SDK pins a
# macro-utils-c revision using the inc/macro_utils/ layout, its CMakeLists
# generates ${CMAKE_BINARY_DIR}/azure_macro_utils/macro_utils.h containing
# #include "macro_utils/macro_utils.h". CMAKE_BINARY_DIR is /wrapper/build,
# because the wrapper pulls the SDK in with add_subdirectory().
#
# This phase builds a different commit, which may pin a macro-utils-c revision
# using the older inc/azure_macro_utils/ layout. /wrapper/build is on the
# include path ahead of ${C_SDK_ROOT}/deps/azure-macro-utils-c/inc, so the
# stale forwarder shadows the real header and its inner include fails with:
#
#   /wrapper/build/azure_macro_utils/macro_utils.h:1:10: fatal error:
#   macro_utils/macro_utils.h: No such file or directory
#
# Removing it is safe for both layouts: an SDK that needs the forwarder
# regenerates it during the cmake step below.
if [ -d "azure_macro_utils" ]; then
    rm -rf azure_macro_utils
    echo "removed stale azure_macro_utils forwarding headers"
fi

cmake -D BUILD_TESTING=OFF -D use_edge_modules=ON  -D skip_samples=ON C_SDK_ROOT=/sdk -DCMAKE_BUILD_TYPE=Debug -D use_amqp=ON -D use_mqtt=ON -D use_http=ON ..
[ $? -eq 0 ] || { echo "cmake failed"; exit 1; }

make edge_e2e_rest_server
[ $? -eq 0 ] || { echo "make failed"; exit 1; }
