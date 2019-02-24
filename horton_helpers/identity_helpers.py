# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import os
import sys
import random
import socket
from config_yaml import ConfigFile
from connection_string import connection_string_to_dictionary


def get_service_connection_string():
    if "IOTHUB_E2E_CONNECTION_STRING" not in os.environ:
        raise Exception(
            "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
        )
        sys.exit(1)
    return os.environ["IOTHUB_E2E_CONNECTION_STRING"]


def get_computer_name():
    if "COMPUTERNAME" in os.environ:
        return os.environ["COMPUTERNAME"]
    else:
        return socket.gethostname()


def get_user_name():
    if "USER" in os.environ:
        return os.environ["USER"]
    elif "USERNAME" in os.environ:
        return os.environ["USERNAME"]
    else:
        return "unkonwn-user-" + str(random.randrange(1000, 9999))


def get_random_device_name():
    return (
        get_computer_name()
        + "_"
        + get_user_name()
        + "_"
        + str(random.randint(10000000, 99999999))
    )


def get_edge_device_id():
    config_file = ConfigFile()
    device_connection_string = config_file.contents["provisioning"][
        "device_connection_string"
    ]

    if device_connection_string:
        return connection_string_to_dictionary(device_connection_string)["DeviceId"]


def ensure_edge_environment_variables():
    get_service_connection_string()

    if not (
        "IOTHUB_E2E_EDGEHUB_DEVICE_ID" in os.environ
        and "IOTHUB_E2E_EDGEHUB_DNS_NAME" in os.environ
    ):
        os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"] = get_computer_name()
        try:
            config_file = ConfigFile()
            device_connection_string = config_file.contents["provisioning"][
                "device_connection_string"
            ]
            if "DeviceId=" in device_connection_string:
                os.environ[
                    "IOTHUB_E2E_EDGEHUB_DEVICE_ID"
                ] = connection_string_to_dictionary(device_connection_string)[
                    "DeviceId"
                ]

        except FileNotFoundError:
            raise Exception(
                "config.yaml not found.  You need to set IOTHUB_E2E_EDGEHUB_DEVICE_ID and IOTHUB_E2E_EDGEHUB_DNS_NAME if you're not running on your edgeHub host"
            )
