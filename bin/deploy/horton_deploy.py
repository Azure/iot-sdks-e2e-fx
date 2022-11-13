# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from connection_string import connection_string_to_sas_token
from iothub_service_helper import IoTHubServiceHelper
from horton_settings import settings
from . import edge_deployment
from . import utilities
import argparse
import os

testMod_host_port = 8099


def _deploy_common(test_image):
    utilities.pull_docker_image(test_image)
    utilities.remove_old_instances()

    settings.horton.image = test_image
    settings.horton.language = utilities.get_language_from_image_name(test_image)
    settings.horton.is_windows = utilities.is_windows()

    settings.horton.id_base = utilities.get_random_device_name()
    settings.horton.machine_name = utilities.get_computer_name()
    settings.horton.time_tag = utilities.get_time_tag()


def _deploy_system_control(network_destination):
    if settings.horton.is_windows:
        settings.system_control.adapter_address = None
    else:
        settings.system_control.test_destination = network_destination
        settings.system_control.host_port = 8140
        settings.system_control.container_port = 8040

        settings.system_control.adapter_address = "http://localhost:{}".format(
            settings.system_control.host_port
        )


def deploy_for_iotedge(test_image):

    _deploy_common(test_image)

    settings.iotedge.iotedge_host_name = utilities.get_computer_name()

    iothub_host_name = connection_string_to_sas_token(
        settings.iothub.connection_string
    )["host"]
    settings.iothub.iothub_host_name = iothub_host_name
    print("Creating new device on hub {}".format(iothub_host_name))
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    settings.iotedge.device_id = settings.horton.id_base + "_iotedge"
    edge_device = iothub_service_helper.create_device(
        settings.iotedge.device_id, is_edge=True
    )

    edge_deployment.add_edge_modules(test_image)
    edge_deployment.set_edge_configuration()

    # default leaf device to use test_module connection.  Fix this in conftest.py if we need to use friend_module
    settings.leaf_device.device_id = settings.horton.id_base + "_leaf_device"
    iothub_service_helper.create_device(
        settings.leaf_device.device_id,
        is_edge=False,
        device_scope=edge_device.device_scope,
    )

    settings.leaf_device.connection_type = "connection_string_with_edge_gateway"
    settings.leaf_device.adapter_address = settings.test_module.adapter_address
    settings.leaf_device.language = settings.test_module.language
    settings.leaf_device.host_port = settings.test_module.host_port
    settings.leaf_device.container_port = settings.test_module.container_port
    settings.leaf_device.container_name = settings.test_module.container_name
    settings.leaf_device.iothub_host_name = iothub_host_name
    settings.leaf_device.object_type = "leaf_device"

    _deploy_system_control(settings.iotedge.iotedge_host_name)

    edge_deployment.set_config_yaml()
    edge_deployment.restart_iotedge()

    print(
        "New IotEdge device created with device_id={}".format(
            settings.iotedge.device_id
        )
    )

    settings.save()


def deploy_for_iothub(test_image):
    _deploy_common(test_image)

    iothub_host_name = connection_string_to_sas_token(
        settings.iothub.connection_string
    )["host"]
    print("Creating new device on hub {}".format(iothub_host_name))
    settings.iothub.iothub_host_name = iothub_host_name

    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    settings.test_device.device_id = settings.horton.id_base + "_test_device"
    settings.test_device.connection_type = "connection_string"
    settings.test_device.host_port = testMod_host_port
    settings.test_device.container_name = "testMod"
    settings.test_device.object_type = "iothub_device"
    settings.test_device.iothub_host_name = iothub_host_name
    utilities.set_args_from_image(settings.test_device, test_image)
    iothub_service_helper.create_device(settings.test_device.device_id)

    settings.test_module.device_id = settings.test_device.device_id
    settings.test_module.module_id = "testMod"
    settings.test_module.connection_type = "connection_string"
    settings.test_module.host_port = testMod_host_port
    settings.test_module.container_name = "testMod"
    settings.test_module.object_type = "iothub_module"
    settings.test_module.iothub_host_name = iothub_host_name
    utilities.set_args_from_image(settings.test_module, test_image)
    iothub_service_helper.create_device_module(
        settings.test_module.device_id, settings.test_module.module_id
    )

    _deploy_system_control(iothub_host_name)

    utilities.create_docker_container(settings.test_module)

    settings.save()


def get_description():
    return "deploy containers for testing"


def set_command_args(parser):
    parser.description = get_description()
    parser.add_argument(
        "deployment_type",
        type=str,
        choices=["iothub", "iotedge"],
        help="type of deployment",
    )

    target_subparsers = parser.add_subparsers(dest="target", required=True)

    image_parser = target_subparsers.add_parser("image", help="deploy image")
    image_parser.add_argument("image_name", type=str, help="image name")

    target_subparsers.add_parser("keep-same", help="keep same target")

    vsts_parser = target_subparsers.add_parser(
        "vsts", help="deploy based on vsts build"
    )
    vsts_parser.add_argument("build_id", type=str, help="vsts build id")
    vsts_parser.add_argument(
        "--language",
        type=str,
        help="sdk language",
        required=True,
        choices=utilities.all_languages,
    )
    vsts_parser.add_argument(
        "--variant", type=str, help="sdk variant", choices=utilities.all_variants
    )

    lkg_parser = target_subparsers.add_parser("lkg", help="deploy based on vsts LKG")
    lkg_parser.add_argument(
        "--language",
        type=str,
        help="sdk language",
        required=True,
        choices=utilities.all_languages,
    )
    lkg_parser.add_argument(
        "--variant", type=str, help="sdk variant", choices=utilities.all_variants
    )


def handle_command_args(args):
    image = None
    if args.target == "image":
        image = args.image_name
        print("Using new image: {}".format(image))
    elif args.target == "lkg":
        if args.variant:
            image = "{}-e2e-v3:lkg-{}".format(args.language, args.variant)
        else:
            image = "{}-e2e-v3:lkg".format(args.language)
        print("Using LKG image: {}".format(image))
    elif args.target == "vsts":
        if args.variant:
            image = "{}-e2e-v3:vsts-{}-{}".format(
                args.language, args.build_id, args.variant
            )
        else:
            image = "{}-e2e-v3:vsts-{}".format(args.language, args.build_id)
        print("Using VSTS image: {}".format(image))
    elif args.target == "keep-same":
        if settings.horton.image:
            image = settings.horton.image
            print("Using previous image: {}".format(image))
        else:
            print("No previous image.  You need to specify an image")
            parser.usage()
            exit(1)

    utilities.get_language_from_image_name(
        image
    )  # validate image name before continuing

    if "/" not in image:
        if "IOTHUB_E2E_REPO_ADDRESS" in os.environ:
            repo_addr = os.environ["IOTHUB_E2E_REPO_ADDRESS"]
            image = "{}/{}".format(repo_addr, image)

    if args.deployment_type == "iothub":
        deploy_for_iothub(image)
    elif args.deployment_type == "iotedge":
        deploy_for_iotedge(image)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="horton_deploy")
    set_command_args(parser)
    args = parser.parse_args()
    handle_command_args(args)
