#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from edgehub_factory import createNewHubInstance
from connection_string import connection_string_to_sas_token
from config_yaml import ConfigFile
from identity_helpers import ensure_edge_environment_variables
from service_helper import Helper
import os
import sys

ensure_edge_environment_variables()

if "IOTHUB_E2E_CONNECTION_STRING" not in os.environ:
    print(
        "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
    )
    sys.exit(1)

service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
host = connection_string_to_sas_token(service_connection_string)["host"]
print("Creating new device on hub {}".format(host))

if "IOTHUB_E2E_EDGEHUB_DEVICE_ID" in os.environ:
    old_edgehub_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]
    old_edgehub_leaf_device = "{}_leaf_device".format(old_edgehub_device_id)
    helper = Helper(service_connection_string)
    if helper.try_delete_device(old_edgehub_device_id):
        print("deleted {}".format(old_edgehub_device_id))
    if helper.try_delete_device(old_edgehub_leaf_device):
        print("deleted {}".format(old_edgehub_leaf_device))
hub = createNewHubInstance(service_connection_string)
hub.deployModules("friend,node")

print("updating config.yaml to insert connection string")
config_file = ConfigFile()
config_file.contents["provisioning"][
    "device_connection_string"
] = hub.edge_hub_connection_string

if (
    "IOTEDGE_DEBUG_LOG" in os.environ
    and os.environ["IOTEDGE_DEBUG_LOG"].lower() == "true"
):
    print("IOTEDGE_DEBUG_LOG is set. setting edgeAgent RuntimeLogLevel to debug")
    config_file.contents["agent"]["env"]["RuntimeLogLevel"] = "debug"
else:
    print("IOTEDGE_DEBUG_LOG is not set. clearing edgeAgent RuntimeLogLevel")
    if "RuntimeLogLevel" in config_file.contents["agent"]["env"]:
        del config_file.contents["agent"]["env"]["RuntimeLogLevel"]

config_file.save()
print("config.yaml updated")

print("new edgeHub device created with device_id={}".format(hub.edge_hub_device_id))
