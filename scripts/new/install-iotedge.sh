#!/usr/bin/env bash
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

script_dir=$(cd "$(dirname "$0")" && pwd)

$script_dir/install-microsoft-apt-repo.sh
[ $? -eq 0 ] || { echo "install-microsoft-apt-repo failed"; exit 1; }

# Keep the host daemon on the same release line as the edgeAgent/edgeHub images
# deployed by bin/deploy/edge_configuration.py.  Installing aziot-edge unpinned
# picks up whatever is newest in the Microsoft feed, which is how we ended up
# running a 1.6.0 daemon against 1.4 module images.
aziot_edge_line="${IOTHUB_E2E_AZIOT_EDGE_LINE:-1.5}"

# Newest candidate version on the requested line.  apt-cache madison emits
# "  <package> | <version> | <source>", newest first.
latest_version_on_line() {
    apt-cache madison "$1" 2>/dev/null |
        awk -F'|' -v prefix="${aziot_edge_line}." '
            { gsub(/^[ \t]+|[ \t]+$/, "", $2) }
            index($2, prefix) == 1 { print $2; exit }
        '
}

identity_version=$(latest_version_on_line aziot-identity-service)
edge_version=$(latest_version_on_line aziot-edge)

if [ -z "${edge_version}" ] || [ -z "${identity_version}" ]; then
    # The Microsoft repo may already have been registered by the agent image, in
    # which case install-microsoft-apt-repo.sh returns early without refreshing
    # the package lists.  Refresh them once and look again.
    sudo apt-get update
    [ $? -eq 0 ] || { echo "apt update failed"; exit 1; }

    identity_version=$(latest_version_on_line aziot-identity-service)
    edge_version=$(latest_version_on_line aziot-edge)
fi

if [ -z "${edge_version}" ] || [ -z "${identity_version}" ]; then
    echo "ERROR: no aziot-edge/aziot-identity-service package on the ${aziot_edge_line} line"
    apt-cache madison aziot-edge aziot-identity-service
    exit 1
fi

# aziot-edge depends on a matching aziot-identity-service, so both are pinned.
# --allow-downgrades covers agent images that ship a newer daemon preinstalled.
echo "Installing aziot-identity-service=${identity_version} and aziot-edge=${edge_version}"
sudo apt-get install -y --allow-downgrades \
    "aziot-identity-service=${identity_version}" \
    "aziot-edge=${edge_version}"
[ $? -eq 0 ] || { echo "apt-get install aziot-edge failed"; exit 1; }

iotedge --version