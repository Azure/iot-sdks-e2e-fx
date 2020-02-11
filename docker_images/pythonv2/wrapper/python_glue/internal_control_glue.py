# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import heap_check
from azure.iot.device import IoTHubModuleClient
from azure.iot.device.common.pipeline import pipeline_stages_base

logger = logging.getLogger(__name__)

do_async = False


def log_message(msg):
    if isinstance(msg, dict) and "message" in msg:
        print(msg["message"])
    else:
        print(str(msg))


def set_flags(flags):
    global do_async
    logger.info("setting flags to {}".format(flags))
    if "test_async" in flags and flags["test_async"]:
        do_async = True


def get_capabilities():
    reconnect_stage = pipeline_stages_base.ReconnectStage()
    new_python_reconnect = True if getattr(reconnect_stage, "state", None) else False
    caps = {
        "flags": {
            "supports_async": True,
            "security_messages": True,
            "v2_connect_group": True,
            "dropped_connection_tests": True,
            "net_control_app": True,
            "checks_for_leaks": True,
            "new_python_reconnect": new_python_reconnect,
        },
        "skip_list": [],
    }
    return caps


def send_command(cmd):
    if cmd == "check_for_leaks":
        heap_check.assert_all_iothub_objects_have_been_collected()
    else:
        raise Exception("Unsupported Command")
