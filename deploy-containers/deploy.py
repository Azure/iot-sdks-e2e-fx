# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import connection_string_to_sas_token
from iothub_service_helper import IoTHubServiceHelper
from horton_settings import settings
import edge_deployment
import utilities

testMod_host_port = 8099


def deploy_for_iotedge(testMod_image):
    utilities.remove_old_instances()

    settings.iotedge.hostname = utilities.get_computer_name()
    device_id_base = utilities.get_random_device_name()

    host = connection_string_to_sas_token(settings.iothub.connection_string)["host"]
    print("Creating new device on hub {}".format(host))
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    settings.iotedge.device_id = device_id_base + "_iotedge"
    iothub_service_helper.create_device(settings.iotedge.device_id, True)

    edge_deployment.add_edge_modules(testMod_image)
    edge_deployment.set_edge_configuration()

    # default leaf device to use test_module connection.  Fix this in conftest.py if we need to use friend_module
    settings.leaf_device.device_id = device_id_base + "_leaf_device"
    iothub_service_helper.create_device(settings.leaf_device.device_id, False)

    settings.leaf_device.connection_type = "connection_string_with_edge_gateway"
    settings.leaf_device.adapter_address = settings.test_module.adapter_address
    settings.leaf_device.language = settings.test_module.language
    settings.leaf_device.host_port = settings.test_module.host_port
    settings.leaf_device.container_port = settings.test_module.container_port

    edge_deployment.set_config_yaml()
    edge_deployment.restart_iotedge()

    print(
        "New IotEdge device created with device_id={}".format(
            settings.iotedge.device_id
        )
    )


def deploy_for_iothub_old(testMod_image):
    deploy_for_iotedge(testMod_image)

    settings.test_device.device_id = settings.leaf_device.device_id
    settings.test_device.language = settings.test_module.language
    settings.test_device.adapter_address = settings.test_module.adapter_address
    settings.test_device.connection_type = "connection_string"
    settings.test_device.host_port = settings.test_module.host_port
    settings.test_device.container_port = settings.test_module.container_port
    settings.test_device.container_name = "hortonObjectUnderTest"

    settings.test_module.connection_type = "connection_string"

    settings.clear_object(settings.leaf_device)
    settings.clear_object(settings.friend_module)

    settings.save()


def create_docker_container(obj):
    utilities.run_shell_command("sudo -n docker stop {}".format(obj.container_name))
    utilities.run_shell_command("sudo -n docker rm {}".format(obj.container_name))
    utilities.run_shell_command(
        "docker run -d -p {host_port_1}:{container_port_1} -p {host_port_2}:{container_port_2} --name {name} --restart unless-stopped --cap-add NET_ADMIN --cap-add NET_RAW {image}".format(
            host_port_1=obj.host_port,
            container_port_1=obj.container_port,
            host_port_2=obj.host_port + 100,
            container_port_2=22,
            name=obj.container_name,
            image=obj.image,
        )
    )


def deploy_for_iothub(testMod_image):
    utilities.remove_old_instances()

    device_id_base = utilities.get_random_device_name()

    host = connection_string_to_sas_token(settings.iothub.connection_string)["host"]
    print("Creating new device on hub {}".format(host))
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    settings.test_device.device_id = device_id_base + "_test_device"
    settings.test_device.connection_type = "connection_string"
    settings.test_device.host_port = testMod_host_port
    settings.test_device.container_name = "testMod"
    utilities.set_args_from_image(settings.test_device, testMod_image)
    iothub_service_helper.create_device(settings.test_device.device_id)

    settings.test_module.device_id = settings.test_device.device_id
    settings.test_module.module_id = "testMod"
    settings.test_module.connection_type = "connection_string"
    settings.test_module.host_port = testMod_host_port
    settings.test_module.container_name = "testMod"
    utilities.set_args_from_image(settings.test_module, testMod_image)
    iothub_service_helper.create_device_module(
        settings.test_module.device_id, settings.test_module.module_id
    )

    create_docker_container(settings.test_module)

    settings.save()
