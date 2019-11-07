# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import connection_string_to_sas_token
from config_yaml import ConfigFile
from iothub_service_helper import IoTHubServiceHelper
from horton_settings import settings
from edge_configuration import EdgeConfiguration
import base64
import glob
import os
import sys
import time
import subprocess
import socket
import random
import string


friendMod_container_port = 8080
friendMod_host_port = 8098
friendMod_language = "node"

testMod_host_port = 8099

iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)


def get_computer_name():
    if "COMPUTERNAME" in os.environ:
        return os.environ["COMPUTERNAME"]
    else:
        return socket.gethostname()


def get_random_device_name(extension=""):
    return (
        get_computer_name()
        + "_"
        + "".join(random.choice(string.ascii_uppercase) for _ in range(3))
        + "_"
        + str(random.randint(100, 999))
        + extension
    )


device_id_base = get_random_device_name()


def run_shell_command(cmd):
    print("running [{}]".format(cmd))
    try:
        return subprocess.check_output(cmd.split(" ")).decode("utf-8").splitlines()
    except subprocess.CalledProcessError as e:
        print("Error spawning {}".format(e.cmd))
        print("Process returned {}".format(e.returncode))
        print("process output: {}".format(e.output))
        raise


def get_edge_ca_cert_base64():
    filename = glob.glob("/var/lib/iotedge/hsm/certs/edge_owner_ca*.pem")[0]
    cert = run_shell_command("sudo -n cat {}".format(filename))
    return base64.b64encode("\n".join(cert).encode("ascii")).decode("ascii")


def get_container_port_from_language(language):
    port_map = {
        "node": 8080,
        "pythonv1": 8080,
        "c": 8082,
        "csharp": 80,
        "java": 8080,
        "pythonv2": 8080,
    }
    return port_map[language]


def get_language_from_image_name(image):
    languages = ["pythonv2", "pythonv1", "java", "csharp", "node", "c"]
    for language in languages:
        if language + "-e2e" in image:
            return language
    print("Error: could not determine language from image name {}".format(image))
    sys.exit(1)


def set_edge_configuration(testMod_image):
    edge_config = EdgeConfiguration()

    # Add friend_module

    friendMod_image = (
        os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/default-friend-module:latest"
    )
    edge_config.add_module_container(
        "friendMod", friendMod_image, friendMod_container_port, friendMod_host_port
    )
    settings.friend_module.device_id = settings.iotedge.device_id
    settings.friend_module.module_id = "friendMod"
    settings.friend_module.language = friendMod_language
    settings.friend_module.adapter_address = "http://{}:{}".format(
        "localhost", friendMod_host_port
    )
    settings.friend_module.connection_type = "environment"
    settings.friend_module.host_port = friendMod_host_port
    settings.friend_module.container_port = get_container_port_from_language(
        friendMod_language
    )

    # Add test_module

    testMod_language = get_language_from_image_name(testMod_image)
    testMod_container_port = get_container_port_from_language(testMod_language)

    edge_config.add_module_container(
        "testMod", testMod_image, testMod_container_port, testMod_host_port
    )
    edge_config.add_routes_for_module("testMod")

    settings.test_module.device_id = settings.iotedge.device_id
    settings.test_module.module_id = "testMod"
    settings.test_module.language = testMod_language
    settings.test_module.adapter_address = "http://{}:{}".format(
        "localhost", testMod_host_port
    )
    settings.test_module.connection_type = "environment"
    settings.test_module.host_port = testMod_host_port
    settings.test_module.container_port = testMod_container_port

    # apply the configuraiton
    iothub_service_helper.apply_configuration(
        settings.iotedge.device_id, edge_config.get_module_config()
    )

    settings.save()


def set_config_yaml():
    settings.iotedge.connection_string = iothub_service_helper.get_device_connection_string(
        settings.iotedge.device_id
    )

    print("updating config.yaml to insert connection string")
    config_file = ConfigFile()
    config_file.contents["provisioning"][
        "device_connection_string"
    ] = settings.iotedge.connection_string

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
    settings.save()
    print("config.yaml updated")


def populate_credentials():

    settings.iotedge.ca_cert_base64 = get_edge_ca_cert_base64()

    for device in (settings.leaf_device, settings.test_device):
        if device.device_id:
            if device.connection_type.startswith("connection_string"):
                device.connection_string = iothub_service_helper.get_device_connection_string(
                    device.device_id
                )
                if device.connection_type.endswith("_with_edge_gateway"):
                    device.connection_string += ";GatewayHostName={}".format(
                        settings.iotedge.hostname
                    )
                print(
                    "Added connection string for {} device {}".format(
                        device.name, device.device_id
                    )
                )

    for module in (settings.test_module, settings.friend_module):
        if module.module_id:

            if (
                module.connection_type.startswith("connection_string")
                or module.connection_type == "environment"
            ):
                module.connection_string = iothub_service_helper.get_module_connection_string(
                    module.device_id, module.module_id
                )
                if (
                    module.connection_type.endswith("_with_edge_gateway")
                    or module.connection_type == "environment"
                ):
                    module.connection_string += ";GatewayHostName={}".format(
                        settings.iotedge.hostname
                    )

                "Added connection string for {} module {},{}".format(
                    module.name, module.device_id, module.module_id
                )
    settings.save()


def restart_iotedge():
    run_shell_command("sudo -n systemctl restart iotedge")


def remove_instance(settings_object):
    if settings_object.device_id:
        iothub_service_helper.try_delete_device(settings_object.device_id)
        print(
            "Removed {} device with id {}".format(
                settings_object.name, settings_object.device_id
            )
        )
    settings.clear_object(settings_object)
    settings.save()


def remove_old_instances():
    remove_instance(settings.test_module)
    remove_instance(settings.friend_module)
    remove_instance(settings.iotedge)
    remove_instance(settings.test_device)
    remove_instance(settings.leaf_device)


def deploy_for_iotedge(testMod_image):
    remove_old_instances()

    settings.iotedge.hostname = get_computer_name()

    host = connection_string_to_sas_token(settings.iothub.connection_string)["host"]
    print("Creating new device on hub {}".format(host))
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    settings.iotedge.device_id = device_id_base + "_iotedge"
    iothub_service_helper.create_device(settings.iotedge.device_id, True)

    set_edge_configuration(testMod_image)

    settings.leaf_device.device_id = device_id_base + "_leaf_device"
    iothub_service_helper.create_device(settings.leaf_device.device_id, False)

    # default leaf device to use test_module connection.  Fix this in conftest.py if we need to use friend_module
    settings.leaf_device.connection_type = "connection_string_with_edge_gateway"
    settings.leaf_device.adapter_address = settings.test_module.adapter_address
    settings.leaf_device.language = settings.test_module.language
    settings.leaf_device.host_port = settings.test_module.host_port
    settings.leaf_device.container_port = settings.test_module.container_port

    set_config_yaml()
    restart_iotedge()

    print(
        "New IotEdge device created with device_id={}".format(
            settings.iotedge.device_id
        )
    )


def deploy_for_iothub(testMod_image):
    deploy_for_iotedge(testMod_image)

    settings.test_device.device_id = settings.leaf_device.device_id
    settings.test_device.language = settings.test_module.language
    settings.test_device.adapter_address = settings.test_module.adapter_address
    settings.test_device.connection_type = "connection_string"
    settings.test_device.host_port = settings.test_module.host_port
    settings.test_device.container_port = settings.test_module.container_port

    settings.test_module.connection_type = "connection_string"

    settings.clear_object(settings.leaf_device)
    settings.clear_object(settings.friend_module)

    settings.save()
