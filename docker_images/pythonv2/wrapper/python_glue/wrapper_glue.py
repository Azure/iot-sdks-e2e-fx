# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.controllers import module_controller
from swagger_server.controllers import device_controller
import internal_wrapper_glue


def log_message(msg):
    internal_wrapper_glue.log_message(msg)


def cleanup_resources():
    module_controller.module_glue.cleanup_resources()
    device_controller.device_glue.cleanup_resources()


def set_flags(flags):
    internal_wrapper_glue.set_flags(flags)


def get_capabilities():
    return internal_wrapper_glue.get_capabilities()


def network_disconnect(disconnect_type):
    print("wrapper disconnect")
    return internal_wrapper_glue.network_disconnect(disconnect_type)


def network_reconnect():
    return internal_wrapper_glue.network_reconnect()
