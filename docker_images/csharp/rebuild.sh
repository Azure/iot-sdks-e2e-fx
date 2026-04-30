# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
#
# TFM notes (azure-iot-sdk-csharp@main, Linux):
#   device  csproj multi-targets: net8.0;netstandard2.1;netstandard2.0
#   service csproj multi-targets: net6.0;netstandard2.1;netstandard2.0
#   wrapper csproj                net8.0 (ASP.NET Core 8 web SDK)
# Service has no net8.0 target on Linux, so publish it as net6.0; the wrapper
# runs on .NET 8 runtime which forward-loads net6.0 libraries fine.

cd /sdk/iothub/device/src
[ $? -eq 0 ] || { echo "cd device failed"; exit 1; }

dotnet publish --no-dependencies --output /app/ --framework=net8.0
[ $? -eq 0 ] || { echo "publish device failed"; exit 1; }

cd /sdk/iothub/service/src
[ $? -eq 0 ] || { echo "cd service failed"; exit 1; }

dotnet publish --no-dependencies --output /app/ --framework=net6.0
[ $? -eq 0 ] || { echo "publish service failed"; exit 1; }

if [ -d "/wrapper/src" ]; then
    cd /wrapper/src
    [ $? -eq 0 ] || { echo "cd wrapper failed"; exit 1; }

    dotnet publish --no-dependencies --output /app/ --framework=net8.0 edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

