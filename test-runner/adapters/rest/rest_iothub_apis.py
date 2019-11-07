# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from .. import adapter_config
from .rest_decorators import log_entry_and_exit
from ..decorators import emulate_async
from ..abstract_iothub_apis import (
    AbstractDeviceApi,
    AbstractModuleApi,
    AbstractServiceApi,
    AbstractRegistryApi,
)


class ServiceConnectDisconnect(object):
    @log_entry_and_exit(print_args=False)
    def connect_sync(self, connection_string):
        result = self.rest_endpoint.connect(
            connection_string, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def disconnect_sync(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""


class Connect(object):
    @log_entry_and_exit(print_args=False)
    def connect_sync(self, transport, connection_string, ca_certificate):
        result = self.rest_endpoint.connect(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def disconnect_sync(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    def create_from_connection_string_sync(
        self, transport, connection_string, ca_certificate
    ):
        result = self.rest_endpoint.create_from_connection_string(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def create_from_x509_sync(self, transport, x509):
        result = self.rest_endpoint.create_from_x509(
            transport, x509, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @emulate_async
    @log_entry_and_exit
    def connect2(self):
        if self.connection_id:
            self.rest_endpoint.connect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )

    @emulate_async
    @log_entry_and_exit
    def reconnect(self, force_password_renewal=False):
        if self.connection_id:
            self.rest_endpoint.reconnect(
                self.connection_id,
                force_password_renewal,
                timeout=adapter_config.default_api_timeout,
            )

    @emulate_async
    @log_entry_and_exit
    def disconnect2(self):
        if self.connection_id:
            self.rest_endpoint.disconnect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    def destroy_sync(self):
        if self.connection_id:
            self.rest_endpoint.destroy(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)


class ConnectFromEnvironment(object):
    @log_entry_and_exit
    def connect_from_environment_sync(self, transport):
        result = self.rest_endpoint.connect_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def create_from_environment_sync(self, transport):
        result = self.rest_endpoint.create_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id


class Twin(object):
    @emulate_async
    @log_entry_and_exit
    def enable_twin(self):
        return self.rest_endpoint.enable_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def get_twin(self):
        return self.rest_endpoint.get_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def patch_twin(self, patch):
        self.rest_endpoint.patch_twin(
            self.connection_id, patch, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def wait_for_desired_property_patch(self):
        return self.rest_endpoint.wait_for_desired_properties_patch(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )


class HandleMethods(object):
    @emulate_async
    @log_entry_and_exit
    def enable_methods(self):
        return self.rest_endpoint.enable_methods(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    """
    roundtrip_method_call
    Description: This is a poorly named method. It is essentially create a
    method callback and then wait for a method call.
    """

    @emulate_async
    @log_entry_and_exit
    def roundtrip_method_call(
        self, method_name, status_code, request_payload, response_payload
    ):
        request_and_response = {
            "requestPayload": request_payload,
            "responsePayload": response_payload,
            "statusCode": status_code,
        }
        return self.rest_endpoint.roundtrip_method_call(
            self.connection_id,
            method_name,
            request_and_response,
            timeout=adapter_config.default_api_timeout,
        )


class Telemetry(object):
    @emulate_async
    @log_entry_and_exit
    def send_event(self, body):
        self.rest_endpoint.send_event(
            self.connection_id, body, timeout=adapter_config.default_api_timeout
        )


class InputsAndOutputs(object):
    @emulate_async
    @log_entry_and_exit
    def send_output_event(self, output_name, body):
        self.rest_endpoint.send_output_event(
            self.connection_id,
            output_name,
            body,
            timeout=adapter_config.default_api_timeout,
        )

    @emulate_async
    @log_entry_and_exit
    def enable_input_messages(self):
        return self.rest_endpoint.enable_input_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def wait_for_input_event(self, input_name):
        return self.rest_endpoint.wait_for_input_message(
            self.connection_id, input_name, timeout=adapter_config.default_api_timeout
        )


class InvokeMethods(object):
    @emulate_async
    @log_entry_and_exit
    def call_module_method(self, device_id, module_id, method_invoke_parameters):
        return self.rest_endpoint.invoke_module_method(
            self.connection_id,
            device_id,
            module_id,
            method_invoke_parameters,
            timeout=adapter_config.default_api_timeout,
        )

    @emulate_async
    @log_entry_and_exit
    def call_device_method(self, device_id, method_invoke_parameters):
        return self.rest_endpoint.invoke_device_method(
            self.connection_id,
            device_id,
            method_invoke_parameters,
            timeout=adapter_config.default_api_timeout,
        )


class ConnectionStatus(object):
    @emulate_async
    @log_entry_and_exit
    def get_connection_status(self):
        return self.rest_endpoint.get_connection_status(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def wait_for_connection_status_change(self):
        return self.rest_endpoint.wait_for_connection_status_change(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )


class C2d(object):
    @emulate_async
    @log_entry_and_exit
    def enable_c2d(self):
        self.rest_endpoint.enable_c2d_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def wait_for_c2d_message(self):
        return self.rest_endpoint.wait_for_c2d_message(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )


class ServiceSideOfTwin(object):
    @emulate_async
    @log_entry_and_exit
    def get_module_twin(self, device_id, module_id):
        return self.rest_endpoint.get_module_twin(
            self.connection_id,
            device_id,
            module_id,
            timeout=adapter_config.default_api_timeout,
        )

    @emulate_async
    @log_entry_and_exit
    def patch_module_twin(self, device_id, module_id, patch):
        self.rest_endpoint.patch_module_twin(
            self.connection_id,
            device_id,
            module_id,
            patch,
            timeout=adapter_config.default_api_timeout,
        )

    @emulate_async
    @log_entry_and_exit
    def get_device_twin(self, device_id):
        return self.rest_endpoint.get_device_twin(
            self.connection_id, device_id, timeout=adapter_config.default_api_timeout
        )

    @emulate_async
    @log_entry_and_exit
    def patch_device_twin(self, device_id, patch):
        self.rest_endpoint.patch_device_twin(
            self.connection_id,
            device_id,
            patch,
            timeout=adapter_config.default_api_timeout,
        )


class DeviceApi(
    Connect, C2d, Telemetry, Twin, HandleMethods, ConnectionStatus, AbstractDeviceApi
):
    def __init__(self, hostname):
        self.wrapper_rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(
            hostname
        ).wrapper
        self.wrapper_rest_endpoint.config.retry_policy.retries = 0
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).device
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""


class ModuleApi(
    Connect,
    ConnectFromEnvironment,
    Telemetry,
    Twin,
    InputsAndOutputs,
    HandleMethods,
    InvokeMethods,
    ConnectionStatus,
    AbstractModuleApi,
):
    def __init__(self, hostname):
        self.wrapper_rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(
            hostname
        ).wrapper
        self.wrapper_rest_endpoint.config.retry_policy.retries = 0
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).module
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""


class RegistryApi(ServiceConnectDisconnect, ServiceSideOfTwin, AbstractRegistryApi):
    def __init__(self, hostname):
        self.wrapper_rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(
            hostname
        ).wrapper
        self.wrapper_rest_endpoint.config.retry_policy.retries = 0
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).registry
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""


class ServiceApi(ServiceConnectDisconnect, InvokeMethods, AbstractServiceApi):
    def __init__(self, hostname):
        self.wrapper_rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(
            hostname
        ).wrapper
        self.wrapper_rest_endpoint.config.retry_policy.retries = 0
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).service
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
