# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import leak_check
import os
import gc
import platform

logger = logging.getLogger(__name__)

do_async = False
sas_renewal_interval = None


tracker = leak_check.LeakTracker()
tracker.add_tracked_module("azure.iot.device")
tracker.set_baseline()

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
        sas_renewal_interval = flags["sas_renewal_interval"] + DEFAULT_SAS_MARGIN
        print(
            "Setting sas_renewal_interval to {} + a margin of {} ".format(
                sas_renewal_interval, DEFAULT_SAS_MARGIN
            )
        )


def get_capabilities_sync():
    caps = {
        "flags": {
            "v2_connect_group": True,
            "system_control_app": True,
            "checks_for_leaks": True,
        }
    }
    return caps


def send_command_sync(cmd):
    if cmd == "check_for_leaks":
        # If you temporarily comment this out, uncomment the log line so you don't spend
        # many hours tracking down bug that should have been caught here when you  don't
        # remember that you commented this out.
        # Not that this has ever happened to me.
        tracker.check_for_new_leaks()
        # logger.info("NOT CHECCKING FOR LEAKS")
    else:
        raise Exception("Unsupported Command")


def get_wrapper_stats_sync():
    return {
        "language": "python",
        "languageVersion": platform.python_version(),
        "wrapperGcObjectCount": len(gc.get_objects()),
        "wrapperPid": os.getpid(),
    }
