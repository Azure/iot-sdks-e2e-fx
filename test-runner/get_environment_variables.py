#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import parseConnectionString, connectionStringToDictionary
from edgehub_factory import useExistingHubInstance
import os
import sys
import string
from config_yaml import ConfigFile

linux = True


def usage():
    print("Usage get_environment_variables.py [OS]")
    print('OS can be one of "windows" or "linux"')
    print("os will be autodetected ")
    sys.exit(1)


def print_env(env):
    if env in os.environ:
        if linux:
            print('export {}="{}"'.format(env, os.environ[env]))
        else:
            print("set {}={}".format(env, os.environ[env]))


def verifyEnvironmentVariables():
    if not "IOTHUB_E2E_CONNECTION_STRING" in os.environ:
        print(
            "ERROR: Iothub connection string not set in IOTHUB_E2E_CONNECTION_STRING environment variable."
        )
        sys.exit(1)

    if not (
        "IOTHUB_E2E_EDGEHUB_DEVICE_ID" in os.environ
        and "IOTHUB_E2E_EDGEHUB_DNS_NAME" in os.environ
    ):
        try:
            config_file = ConfigFile()
            device_connection_string = config_file.contents["provisioning"][
                "device_connection_string"
            ]
            if "DeviceId=" in device_connection_string:
                os.environ[
                    "IOTHUB_E2E_EDGEHUB_DEVICE_ID"
                ] = connectionStringToDictionary(device_connection_string)["DeviceId"]
            os.environ["IOTHUB_E2E_EDGEHUB_DNS_NAME"] = config_file.contents["hostname"]

        except FileNotFoundError:
            raise Exception(
                "config.yaml not found.  You need to set IOTHUB_E2E_EDGEHUB_DEVICE_ID and IOTHUB_E2E_EDGEHUB_DNS_NAME if you're not running on your edgeHub host"
            )


if __name__ == "__main__":
    verifyEnvironmentVariables()

    if len(sys.argv) == 1:
        if ("OS" in os.environ) and (os.environ["OS"] == "Windows_NT"):
            linux = False
    elif len(sys.argv) == 2:
        if sys.argv[1] == "linux":
            linux = True
        elif sys.argv[1] == "windows":
            linux = False
        else:
            usage()
    else:
        usage()

    service_connection_string = os.environ["IOTHUB_E2E_CONNECTION_STRING"]
    edge_hub_device_id = os.environ["IOTHUB_E2E_EDGEHUB_DEVICE_ID"]
    hub = useExistingHubInstance(service_connection_string, edge_hub_device_id)
    host = parseConnectionString(service_connection_string)["host"]

    print_env("IOTHUB_E2E_CONNECTION_STRING")
    print_env("IOTHUB_E2E_EDGEHUB_DNS_NAME")
    print_env("IOTHUB_E2E_EDGEHUB_DEVICE_ID")
    print_env('IOTHUB_E2E_REPO_ADDRESS')
    # print_env('IOTHUB_E2E_REPO_USER')
    # print_env('IOTHUB_E2E_REPO_PASSWORD')
    print_env("IOTHUB_E2E_EDGEHUB_CA_CERT")
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_REGISTRY')
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_AGENTIMAGE')
    # print_env('IOTHUB_E2E_EDGE_PRIVATE_HUBIMAGE')
