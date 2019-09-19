# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging

logger = logging.getLogger(__name__)

do_async = False


def log_message(msg):
    if "message" in msg:
        print(msg["message"])
    else:
        print(str(msg))


def set_flags(flags):
    global do_async
    logger.info("setting flags to {}".format(flags))
    if "test_async" in flags and flags["test_async"]:
        do_async = True


def get_capabilities():
    return {
        "flags": {
            "supports_async": True,
            "security_messages": True,
            "new_message_format": True,
        },
        "skip_list": ["invokesModuleMethodCalls", "invokesDeviceMethodCalls"],
    }


def network_disconnect(disconnect_type):
    pass
    # BKTODO


def network_reconnect():
    pass
    # BKTODO
