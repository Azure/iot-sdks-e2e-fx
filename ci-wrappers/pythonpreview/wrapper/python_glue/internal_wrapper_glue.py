#!/usr/bin/env python

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
        "flags": {"supports_async": True},
        "skip_list": [
            "invokesModuleMethodCalls",
            "invokesDeviceMethodCalls",
            "supportsTwin",
            "handlesLoopbackMessages",
            "module_under_test_has_device_wrapper",
        ],
    }
