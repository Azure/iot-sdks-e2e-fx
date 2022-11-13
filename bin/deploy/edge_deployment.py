# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import os
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


def update_config_toml():
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)
    settings.iotedge.connection_string = iothub_service_helper.get_device_connection_string(
        settings.iotedge.device_id
    )
    settings.save()

    print("updating config.toml to insert connection string")
    utilities.run_elevated_shell_command(
        "iotedge config mp --force --connection-string "
        "{}"
        "".format(settings.iotedge.connection_string)
    )
    print("config.toml updated")

    utilities.run_elevated_shell_command("iotedge config apply")
    print("config.toml changes applied")
