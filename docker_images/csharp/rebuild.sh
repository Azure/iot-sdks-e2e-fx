# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

cd /sdk/shared/src
[ $? -eq 0 ] || { echo "cd shared failed"; exit 1; }

dotnet publish --no-dependencies --output /app/ --framework=netstandard2.0
[ $? -eq 0 ] || { echo "publish shared failed"; exit 1; }

cd /sdk/iothub/device/src
[ $? -eq 0 ] || { echo "cd device failed"; exit 1; }

dotnet publish --no-dependencies --output /app/ --framework=netstandard2.0
[ $? -eq 0 ] || { echo "publish device failed"; exit 1; }

cd /sdk/iothub/service/src
[ $? -eq 0 ] || { echo "cd service failed"; exit 1; }

dotnet publish --no-dependencies --output /app/ --framework=netstandard2.0
[ $? -eq 0 ] || { echo "publish service failed"; exit 1; }

if [ -d "/wrapper/src" ]; then
    cd /wrapper/src
    [ $? -eq 0 ] || { echo "cd wrapper failed"; exit 1; }

    dotnet publish --no-dependencies --output /app/ --framework=netcoreapp3.0 edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

