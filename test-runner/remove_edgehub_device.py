#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from edgehub_factory import createNewHubInstance
from connection_string import parseConnectionString
from config_yaml import ConfigFile
from get_environment_variables import verifyEnvironmentVariables
from service_helper import Helper
import os
import sys

print("Removing edgehub device")

verifyEnvironmentVariables()

if not "IOTHUB_E2E_CONNECTION_STRING" in os.environ:
    print(
        "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
    )
    sys.exit(1)

service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]

if "IOTHUB_E2E_EDGEHUB_DEVICE_ID" in os.environ:
    old_edgehub_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]
    old_edgehub_leaf_device = "{}_leaf_device".format(old_edgehub_device_id)
    helper = Helper(service_connection_string)
    if helper.try_delete_device(old_edgehub_device_id):
        print("deleted {}".format(old_edgehub_device_id))
    if helper.try_delete_device(old_edgehub_leaf_device):
        print("deleted {}".format(old_edgehub_leaf_device))

    print("updating config.yaml to remove strings")
    config_file = ConfigFile()
    config_file.contents["provisioning"][
        "device_connection_string"
    ] = ""

    config_file.save()
    print("config.yaml updated")

    print("edgehub test devices removed")
else:
    print("no devices to remove")
