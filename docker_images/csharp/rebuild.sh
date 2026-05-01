# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.
#
# TFM notes:
#   previews/v2 branch : device & service target netstandard2.0
#   ewertons branch    : device & service target net10.0
#   wrapper            : always targets net10.0 (forward-loads netstandard2.0)
#
# The script auto-detects each SDK project's TFM so the same Dockerfile
# works for both branches.

# Extract the first TFM from a csproj (handles both <TargetFramework> and
# <TargetFrameworks> with semicolon-separated values).
get_tfm() {
    grep -oP '<TargetFrameworks?>\K[^<]+' "$1" | tr ';' '\n' | head -1
}

cd /sdk/iothub/device/src
[ $? -eq 0 ] || { echo "cd device failed"; exit 1; }

DEVICE_TFM=$(get_tfm Microsoft.Azure.Devices.Client.csproj)
DEVICE_TFM=${DEVICE_TFM:-netstandard2.0}
echo "Device TFM: $DEVICE_TFM"

dotnet restore
dotnet publish --no-dependencies --output /app/ --framework=$DEVICE_TFM
[ $? -eq 0 ] || { echo "publish device failed"; exit 1; }

cd /sdk/iothub/service/src
[ $? -eq 0 ] || { echo "cd service failed"; exit 1; }

SERVICE_TFM=$(get_tfm Microsoft.Azure.Devices.csproj)
SERVICE_TFM=${SERVICE_TFM:-netstandard2.0}
echo "Service TFM: $SERVICE_TFM"

dotnet restore
dotnet publish --no-dependencies --output /app/ --framework=$SERVICE_TFM
[ $? -eq 0 ] || { echo "publish service failed"; exit 1; }

if [ -d "/wrapper/src" ]; then
    cd /wrapper/src
    [ $? -eq 0 ] || { echo "cd wrapper failed"; exit 1; }

    dotnet restore
    dotnet publish --no-dependencies --output /app/ --framework=net10.0 edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

