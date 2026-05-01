# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# Publish SDK sub-projects (paths may not exist if the SDK was restructured)
for proj in shared/src iothub/device/src iothub/service/src; do
    if [ -d "/sdk/$proj" ] && ls /sdk/$proj/*.csproj >/dev/null 2>&1; then
        cd /sdk/$proj
        dotnet publish --no-dependencies --output /app/ --framework=netstandard2.0
        [ $? -eq 0 ] || { echo "publish $proj failed"; exit 1; }
    else
        echo "Skipping publish for $proj (no project found)"
    fi
done

if [ -d "/wrapper/src" ]; then
    cd /wrapper/src
    [ $? -eq 0 ] || { echo "cd wrapper failed"; exit 1; }

    dotnet publish --no-dependencies --output /app/ --framework=net8.0 edge-e2e.csproj
    [ $? -eq 0 ] || { echo "publish wrapper failed"; exit 1; }
fi

