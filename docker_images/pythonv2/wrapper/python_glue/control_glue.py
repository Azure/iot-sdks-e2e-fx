# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.controllers import module_controller
from swagger_server.controllers import device_controller
import internal_control_glue


def log_message(msg):
    internal_control_glue.log_message_sync(msg)


def cleanup_resources():
    module_controller.module_glue.cleanup_resources()
    device_controller.device_glue.cleanup_resources()


def set_flags(flags):
    internal_control_glue.set_flags_sync(flags)


def get_capabilities():
    return internal_control_glue.get_capabilities_sync()


def send_command(cmd):
    return internal_control_glue.send_command_sync(cmd)


def get_wrapper_stats():
    return internal_control_glue.get_wrapper_stats_sync()
