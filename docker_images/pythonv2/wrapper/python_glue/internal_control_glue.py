# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import leak_check
from azure.iot.device.common.pipeline import pipeline_stages_base
from azure.iot.device.iothub import abstract_clients

logger = logging.getLogger(__name__)

do_async = False
sas_renewal_interval = None


tracker = leak_check.LeakTracker()
tracker.add_tracked_module("azure.iot.device")
tracker.set_baseline()


# Length of time, in seconds, that a SAS token is valid for.
try:
    ORIGINAL_DEFAULT_SAS_TTL = abstract_clients.DEFAULT_SAS_TTL
except AttributeError:
    ORIGINAL_DEFAULT_SAS_TTL = 0

# SAS renewal margin.  currently hardcoded
DEFAULT_SAS_MARGIN = 120


def log_message_sync(msg):
    if isinstance(msg, dict) and "message" in msg:
        print(msg["message"])
    else:
        print(str(msg))


def set_flags_sync(flags):
    global do_async
    global sas_renewal_interval

    logger.info("setting flags to {}".format(flags))
    # Resist the tempation to use getattr.  We don't want to change flags that aren't populated.
    if "test_async" in flags:
        do_async = flags["test_async"]
    if "sas_renewal_interval" in flags:
        sas_renewal_interval = flags["sas_renewal_interval"]
        print("Setting sas_renewal_interval to {}".format(sas_renewal_interval))


def get_capabilities_sync():
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
            "supports_blob_upload": True,
        },
        "skip_list": [],
    }
    return caps


def send_command_sync(cmd):
    if cmd == "check_for_leaks":
        # tracker.check_for_new_leaks()
        pass
    else:
        raise Exception("Unsupported Command")


def set_sas_interval_sync():
    global sas_renewal_interval
    print("Using sas_renewal_interval of {}".format(sas_renewal_interval))
    if sas_renewal_interval:
        abstract_clients.DEFAULT_SAS_TTL = sas_renewal_interval + DEFAULT_SAS_MARGIN
    else:
        abstract_clients.DEFAULT_SAS_TTL = ORIGINAL_DEFAULT_SAS_TTL
