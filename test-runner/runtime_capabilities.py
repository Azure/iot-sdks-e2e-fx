# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
import adapters
from msrest.exceptions import HttpOperationError
from horton_settings import settings

hardcoded_skip_list = {
    "node": [],
    "csharp": ["module_under_test_has_device_wrapper", "handlesLoopbackMessages"],
    "pythonv1": [
        "module_under_test_has_device_wrapper",
        "invokesModuleMethodCalls",
        "invokesDeviceMethodCalls",
    ],
    "c": ["module_under_test_has_device_wrapper"],
    "java": ["module_under_test_has_device_wrapper", "supportsTwin"],
}

language_has_full_device_client = ("pythonv2",)
language_has_leaf_device_client = ("node",)
language_has_service_client = ("node", "csharp", "javs", "c")


class HortonCapabilities(object):
    def __init__(self):
        self.supports_async = False
        self.new_message_format = False
        self.security_messages = False
        self.v2_connect_group = False
        self.dropped_connection_tests = False


def collect_capabilities():
    # BKTODO: add an under_test flag to settings and make _objects public so we can iterate
    for horton_object in (
        settings.test_module,
        settings.friend_module,
        settings.test_device,
        settings.leaf_device,
    ):
        if horton_object.device_id:
            horton_object.wrapper_api = adapters.create_adapter(
                horton_object.adapter_address, "wrapper"
            )
            try:
                caps = horton_object.wrapper_api.get_capabilities_sync()
            except HttpOperationError:
                caps = None

            horton_object.capabilities = HortonCapabilities()
            if caps:
                flags = caps["flags"]
                for flag_name in flags:
                    setattr(horton_object.capabilities, flag_name, flags[flag_name])
                horton_object.skip_list = list(caps["skip_list"])
            else:
                horton_object.skip_list = hardcoded_skip_list[horton_object.language]

            for flag_name in dir(horton_object.capabilities):
                value = getattr(horton_object.capabilities, flag_name)
                if not callable(value):
                    if not value:
                        horton_object.skip_list.append(flag_name)
