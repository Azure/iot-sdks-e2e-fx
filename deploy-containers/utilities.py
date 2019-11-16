# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import subprocess
import os
import socket
import random
import string
from iothub_service_helper import IoTHubServiceHelper
from horton_settings import settings


def run_shell_command(cmd):
    print("running [{}]".format(cmd))
    try:
        return subprocess.check_output(cmd.split(" ")).decode("utf-8").splitlines()
    except subprocess.CalledProcessError as e:
        print("Error spawning {}".format(e.cmd))
        print("Process returned {}".format(e.returncode))
        print("process output: {}".format(e.output))
        raise


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
    if "default-friend-module" in image:
        return "node"
    languages = ["pythonv2", "pythonv1", "java", "csharp", "node", "c"]
    for language in languages:
        if language + "-e2e" in image:
            return language
    raise Exception(
        "Error: could not determine language from image name {}".format(image)
    )


def set_args_from_image(obj, image):
    obj.language = get_language_from_image_name(image)
    obj.container_port = get_container_port_from_language(obj.language)
    obj.adapter_address = "http://{}:{}".format("localhost", obj.host_port)
    obj.image = image


def remove_instance(settings_object):
    iothub_service_helper = IoTHubServiceHelper(settings.iothub.connection_string)

    if settings_object.device_id:
        iothub_service_helper.try_delete_device(settings_object.device_id)
        print(
            "Removed {} device with id {}".format(
                settings_object.name, settings_object.device_id
            )
        )

    settings.clear_object(settings_object)
    settings.save()


def try_remove_container(container_name):
    try:
        run_shell_command("sudo -n docker stop {}".format(container_name))
    except subprocess.CalledProcessError:
        print("Ignoring failure")
    try:
        run_shell_command("sudo -n docker rm {}".format(container_name))
    except subprocess.CalledProcessError:
        print("Ignoring failure")


def remove_old_instances():
    try:
        run_shell_command("sudo -n systemctl stop iotedge")
    except subprocess.CalledProcessError:
        print("Ignoring failure")

    if settings.test_module.container_name:
        try_remove_container(settings.test_module.container_name)

    remove_instance(settings.test_module)
    remove_instance(settings.friend_module)
    remove_instance(settings.iotedge)
    remove_instance(settings.test_device)
    remove_instance(settings.leaf_device)


def create_docker_container(obj):
    try_remove_container(obj.container_name)

    run_shell_command(
        "docker run -d -p {host_port_1}:{container_port_1} -p {host_port_2}:{container_port_2} --name {name} --restart=on-failure:10 --cap-add NET_ADMIN --cap-add NET_RAW {image}".format(
            host_port_1=obj.host_port,
            container_port_1=obj.container_port,
            host_port_2=obj.host_port + 100,
            container_port_2=22,
            name=obj.container_name,
            image=obj.image,
        )
    )
