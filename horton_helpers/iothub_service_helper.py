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

from msrest.exceptions import HttpOperationError
import connection_string


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

        self.configuration_manager.apply_configuration_on_edge_device(
            device_id, content
        )

    def create_device(self, device_id, is_edge=False):
        print("creating device {}".format(device_id))
        try:
            device = self.registry_manager.get_device(device_id)
            print("using existing device")
        except HttpOperationError:
            device = Device(device_id=device_id)

        if is_edge:
            device.capabilities = DeviceCapabilities(iot_edge=True)

        self.registry_manager.protocol.devices.create_or_update_identity(
            device_id, device
        )

    def create_device_module(self, device_id, module_id):
        print("creating module {}/{}".format(device_id, module_id))
        try:
            module = self.registry_manager.get_module(device_id, module_id)
            print("using existing device module")
        except HttpOperationError:
            module = Module(device_id=device_id, module_id=module_id)

        self.registry_manager.protocol.modules.create_or_update_identity(
            device_id, module_id, module
        )

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
