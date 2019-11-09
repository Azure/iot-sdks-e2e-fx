# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import subprocess
import os
import socket
import random
import string


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
