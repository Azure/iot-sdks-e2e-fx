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

# Suppress CA1859 — the .NET 10 SDK ships newer Roslyn analysers that
# flag this as an error in SDK source we don't own.
SDK_NOWARN="-p:NoWarn=CA1859"

dotnet restore
dotnet publish --no-dependencies --output /app/ --framework=$DEVICE_TFM $SDK_NOWARN
[ $? -eq 0 ] || { echo "publish device failed"; exit 1; }

cd /sdk/iothub/service/src
[ $? -eq 0 ] || { echo "cd service failed"; exit 1; }

SERVICE_TFM=$(get_tfm Microsoft.Azure.Devices.csproj)
SERVICE_TFM=${SERVICE_TFM:-netstandard2.0}
echo "Service TFM: $SERVICE_TFM"

dotnet restore
dotnet publish --no-dependencies --output /app/ --framework=$SERVICE_TFM $SDK_NOWARN
[ $? -eq 0 ] || { echo "publish service failed"; exit 1; }

if [ -d "/wrapper/src" ]; then
    cd /wrapper/src
    [ $? -eq 0 ] || { echo "cd wrapper failed"; exit 1; }

    # When the SDK targets net10.0 the DesiredProperties/ReportedProperties
    # subclasses have been removed and DirectMethodRequest.Payload is public.
    # Pass SDK_NET10 so the wrapper can conditionally compile.
    WRAPPER_DEFINES=""
    if [ "$DEVICE_TFM" = "net10.0" ]; then
        WRAPPER_DEFINES="-p:DefineConstants=SDK_NET10"
        echo "SDK targets net10.0 — adding SDK_NET10 define"
    fi

    dotnet restore
    dotnet publish --no-dependencies --output /app/ --framework=net10.0 $WRAPPER_DEFINES edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

