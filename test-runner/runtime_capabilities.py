# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
import adapters
from msrest.exceptions import HttpOperationError, ClientRequestError
from horton_settings import settings

language_has_full_device_client = ("pythonv2", "node")
language_has_leaf_device_client = ("node",)
language_has_service_client = ("node", "csharp", "java", "c")


class HortonCapabilities(object):
    def __init__(self):
        self.v2_connect_group = False
        self.dropped_connection_tests = False
        self.net_control_app = False
        self.checks_for_leaks = False
        self.new_python_reconnect = False


def collect_capabilities(horton_object):
    if horton_object.device_id:
        horton_object.wrapper_api = adapters.create_adapter(
            horton_object.adapter_address, "wrapper"
        )
        try:
            caps = horton_object.wrapper_api.get_capabilities_sync()
        except (HttpOperationError, ClientRequestError):
            caps = None

        horton_object.capabilities = HortonCapabilities()
        if caps:
            flags = caps["flags"]
            for flag_name in flags:
                setattr(horton_object.capabilities, flag_name, flags[flag_name])


def collect_all_capabilities():
    # BKTODO: add an under_test flag to settings and make _objects public so we can iterate
    for horton_object in (
        settings.leaf_device,
        settings.test_module,
        settings.friend_module,
        settings.test_device,
    ):
        collect_capabilities(horton_object)
