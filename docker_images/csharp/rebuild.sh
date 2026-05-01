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

# ── Analyzer suppressions ──────────────────────────────────────────────
# The .NET 10 SDK ships newer Roslyn analysers that promote certain warnings
# to errors in SDK source we don't own.  Inject NoWarn=CA1859 into
# Directory.Build.targets so it applies automatically to every project
# compiled inside this container, regardless of how dotnet is invoked.
#
# MSBuild walks up from the project dir and stops at the FIRST
# Directory.Build.targets it finds, so we must cover both:
#   /sdk/  – for standalone SDK builds (device, service)
#   /      – for wrapper builds (and anything else)
# If the SDK already ships its own file, we append rather than replace.
inject_nowarn() {
    local targets="$1/Directory.Build.targets"
    local snippet='<PropertyGroup><NoWarn>$(NoWarn);CA1859</NoWarn></PropertyGroup>'
    if [ -f "$targets" ]; then
        # Append our suppression before </Project> if not already present
        if ! grep -q 'CA1859' "$targets"; then
            sed -i "s|</Project>|  ${snippet}\n</Project>|" "$targets"
            echo "Appended NoWarn=CA1859 to existing $targets"
        fi
    else
        cat > "$targets" << DBEOF
<Project>
  ${snippet}
</Project>
DBEOF
        echo "Created $targets (NoWarn CA1859)"
    fi
}
inject_nowarn /sdk
inject_nowarn /
# ────────────────────────────────────────────────────────────────────────

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

