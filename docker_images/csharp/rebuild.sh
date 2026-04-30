# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
#
# TFM notes (azure-iot-sdk-csharp@previews/v2 — the v2 SDK):
#   device  csproj target: netstandard2.0
#   service csproj target: netstandard2.0
#   wrapper csproj target: net8.0 (ASP.NET Core 8 web SDK)
# Wrapper runs on .NET 8 runtime which forward-loads netstandard2.0 fine.

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

    dotnet publish --no-dependencies --output /app/ --framework=net8.0 edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

