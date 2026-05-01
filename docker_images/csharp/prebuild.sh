# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

# Restore SDK sub-projects (paths may not exist if the SDK was restructured)
for proj in shared/src iothub/device/src iothub/service/src; do
    if [ -d "/sdk/$proj" ]; then
        cd /sdk/$proj
        dotnet restore
        [ $? -eq 0 ] || { echo "restore $proj failed"; exit 1; }
    else
        echo "Skipping restore for $proj (directory not found)"
    fi
done

