# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
from config_yaml import ConfigFile
from horton_settings import settings
from .edge_configuration import EdgeConfiguration
from iothub_service_helper import IoTHubServiceHelper
from . import utilities


friendMod_container_port = 8080
friendMod_host_port = 8098
friendMod_language = "node"

testMod_host_port = 8099


def add_edge_modules(testMod_image):
    if utilities.is_pi():
        friendMod_image = (
            os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/default-friend-module:arm64-v2"
        )
    else:
        friendMod_image = (
            os.environ["IOTHUB_E2E_REPO_ADDRESS"] + "/default-friend-module:x64-v2"
        )

    settings.friend_module.host_port = friendMod_host_port
    settings.friend_module.device_id = settings.iotedge.device_id
    settings.friend_module.module_id = "friendMod"
    settings.friend_module.connection_type = "environment"
    settings.friend_module.object_type = "iotedge_module"
    settings.friend_module.container_name = "friendMod"
    settings.friend_module.iothub_host_name = settings.iothub.iothub_host_name
    utilities.set_args_from_image(settings.friend_module, friendMod_image)

    settings.test_module.host_port = testMod_host_port
    settings.test_module.device_id = settings.iotedge.device_id
    settings.test_module.module_id = "testMod"
    settings.test_module.connection_type = "environment"
    settings.test_module.object_type = "iotedge_module"
    settings.test_module.container_name = "testMod"
    settings.test_module.iothub_host_name = settings.iothub.iothub_host_name
    utilities.set_args_from_image(settings.test_module, testMod_image)


def set_edge_configuration():
    edge_config = EdgeConfiguration()
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    for obj in (settings.test_module, settings.friend_module):
        edge_config.add_module_container(
            obj.module_id, obj.image, obj.container_port, obj.host_port
        )

    edge_config.add_routes_for_module("testMod")

    # apply the configuraiton
    iothub_service_helper.apply_configuration(
        settings.iotedge.device_id, edge_config.get_module_config()
    )

    settings.save()


def set_config_yaml():
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)
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


def restart_iotedge():
    utilities.run_elevated_shell_command("systemctl restart iotedge")
