# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk/shared/src
[ $? -eq 0 ] || { echo "cd shared failed"; exit 1; }

dotnet restore 
[ $? -eq 0 ] || { echo "restore shared failed"; exit 1; }

cd /sdk/iothub/device/src
[ $? -eq 0 ] || { echo "cd device failed"; exit 1; }

dotnet restore
[ $? -eq 0 ] || { echo "restore device failed"; exit 1; }

cd /sdk/iothub/service/src
[ $? -eq 0 ] || { echo "cd service failed"; exit 1; }

dotnet restore 
[ $? -eq 0 ] || { echo "restore service failed"; exit 1; }

