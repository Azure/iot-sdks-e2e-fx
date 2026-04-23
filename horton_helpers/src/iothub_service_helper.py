# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from azure.iot.hub import IoTHubRegistryManager, IoTHubConfigurationManager
from azure.iot.hub.models import (
    Device,
    Module,
    DeviceCapabilities,
    ConfigurationContent,
)

from msrest.exceptions import HttpOperationError, ClientRequestError
import connection_string
import time


def _retry_transient(fn, retries=5, initial_delay=2):
    """Retry an IoT Hub service call on transient errors.

    IoT Hub occasionally returns 503 Service Unavailable or closes
    connections under load.  msrest/urllib3 bubble these up as
    ClientRequestError ("too many 503 error responses") after
    exhausting their internal retries, and HttpOperationError with a
    5xx status for individual 5xx responses.  Wrap deploy-time calls
    with exponential backoff so a transient hiccup doesn't fail the
    whole pipeline job.
    """
    delay = initial_delay
    last_error = None
    for attempt in range(retries):
        try:
            return fn()
        except ClientRequestError as e:
            last_error = e
            msg = str(e)
            if "503" in msg or "502" in msg or "500" in msg or "Connection" in msg:
                if attempt < retries - 1:
                    print(
                        "IoT Hub transient error (attempt {}/{}): {}. Retrying in {}s...".format(
                            attempt + 1, retries, msg[:160], delay
                        )
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, 30)
                    continue
            raise
        except HttpOperationError as e:
            last_error = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (500, 502, 503, 504) and attempt < retries - 1:
                print(
                    "IoT Hub transient {} (attempt {}/{}). Retrying in {}s...".format(
                        status, attempt + 1, retries, delay
                    )
                )
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            raise
    if last_error:
        raise last_error


class IoTHubServiceHelper:
    def __init__(self, service_connection_string):
        self.cn = connection_string.connection_string_to_sas_token(
            service_connection_string
        )
        self.registry_manager = IoTHubRegistryManager.from_connection_string(
            service_connection_string
        )
        self.configuration_manager = IoTHubConfigurationManager.from_connection_string(
            service_connection_string
        )

    def get_device_connection_string(self, device_id):
        device = self.registry_manager.get_device(device_id)

        primary_key = device.authentication.symmetric_key.primary_key
        return (
            "HostName="
            + self.cn["host"]
            + ";DeviceId="
            + device_id
            + ";SharedAccessKey="
            + primary_key
        )

    def get_module_connection_string(self, device_id, module_id):
        module = self.registry_manager.get_module(device_id, module_id)

        primary_key = module.authentication.symmetric_key.primary_key
        return (
            "HostName="
            + self.cn["host"]
            + ";DeviceId="
            + device_id
            + ";ModuleId="
            + module_id
            + ";SharedAccessKey="
            + primary_key
        )

    def apply_configuration(self, device_id, modules_content):
        content = ConfigurationContent(modules_content=modules_content)

        _retry_transient(
            lambda: self.configuration_manager.apply_configuration_on_edge_device(
                device_id, content
            )
        )

    def get_device(self, device_id):
        """Retry-wrapped get_device for transient IoT Hub 5xx errors."""
        return _retry_transient(
            lambda: self.registry_manager.get_device(device_id)
        )

    def create_device(self, device_id, is_edge=False, device_scope=None):
        print("creating device {}".format(device_id))
        try:
            device = _retry_transient(
                lambda: self.registry_manager.get_device(device_id)
            )
            print("using existing device")
        except HttpOperationError:
            device = Device(device_id=device_id)

        if is_edge:
            device.capabilities = DeviceCapabilities(iot_edge=True)

        if device_scope:
            # Both device_scope and parent_scopes must be set for leaf
            # devices.  device_scope tells IoT Hub this device belongs to
            # the edge device's scope, and parent_scopes provides the auth
            # chain that EdgeHub uses for local authentication.  Without
            # device_scope, EdgeHub's on-demand identity refresh fails with
            # "Error while refreshing the service identity" and the leaf
            # device gets "not authenticated locally".
            device.device_scope = device_scope
            device.parent_scopes = [device_scope]
            print("setting device_scope and parent_scopes: {}".format(device_scope))

        device = _retry_transient(
            lambda: self.registry_manager.protocol.devices.create_or_update_identity(
                device_id, device
            )
        )
        print("device created, device_scope={}, parent_scopes={}".format(
            getattr(device, 'device_scope', None),
            getattr(device, 'parent_scopes', None)))
        return device

    def create_device_module(self, device_id, module_id):
        print("creating module {}/{}".format(device_id, module_id))
        try:
            module = _retry_transient(
                lambda: self.registry_manager.get_module(device_id, module_id)
            )
            print("using existing device module")
        except HttpOperationError:
            module = Module(device_id=device_id, module_id=module_id)

        module = _retry_transient(
            lambda: self.registry_manager.protocol.modules.create_or_update_identity(
                device_id, module_id, module
            )
        )
        return module

    def try_delete_device(self, device_id):
        try:
            self.registry_manager.delete_device(device_id)
            return True
        except HttpOperationError:
            return False

    def try_delete_module(self, device_id, module_id):
        try:
            self.registry_manager.delete_module(device_id, module_id)
            return True
        except HttpOperationError:
            return False
