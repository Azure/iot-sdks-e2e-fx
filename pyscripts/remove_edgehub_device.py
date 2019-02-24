#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import connection_string_to_dictionary
from config_yaml import ConfigFile
from service_helper import Helper
import os
import sys


def remove_edgehub_device():
    print("Removing edgehub device")
    if "IOTHUB_E2E_CONNECTION_STRING" not in os.environ:
        print(
            "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
        )
        sys.exit(1)
    service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]

    config_file = ConfigFile()
    device_connection_string = config_file.contents["provisioning"][
        "device_connection_string"
    ]

    if device_connection_string:
        cn = connection_string_to_dictionary(device_connection_string)
        old_edgehub_device_id = cn["DeviceId"]
        old_edgehub_leaf_device = "{}_leaf_device".format(old_edgehub_device_id)
        helper = Helper(service_connection_string)
        if helper.try_delete_device(old_edgehub_device_id):
            print("deleted {}".format(old_edgehub_device_id))
        if helper.try_delete_device(old_edgehub_leaf_device):
            print("deleted {}".format(old_edgehub_leaf_device))

        print("updating config.yaml to remove strings")
        config_file.contents["provisioning"]["device_connection_string"] = ""

        config_file.save()
        print("config.yaml updated")

        print("edgehub test devices removed")
    else:
        print("no devices to remove")


if __name__ == "__main__":
    remove_edgehub_device()
