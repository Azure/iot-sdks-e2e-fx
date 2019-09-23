# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from multiprocessing.pool import ThreadPool
from .. import adapter_config
from ..decorators import log_entry_and_exit
from ..abstract_iothub_apis import (
    AbstractDeviceApi,
    AbstractModuleApi,
    AbstractServiceApi,
    AbstractRegistryApi,
)

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 5


class ServiceConnectDisconnect(object):
    @log_entry_and_exit(print_args=False)
    def connect(self, connection_string):
        result = self.rest_endpoint.connect(
            connection_string, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""


class Connect(object):
    @log_entry_and_exit(print_args=False)
    def connect(self, transport, connection_string, ca_certificate):
        result = self.rest_endpoint.connect(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def disconnect(self):
        if self.connection_id:
            self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    def create_from_connection_string(
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
    def create_from_x509(self, transport, x509):
        result = self.rest_endpoint.create_from_x509(
            transport, x509, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def connect2(self):
        if self.connection_id:
            self.rest_endpoint.connect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )

    @log_entry_and_exit
    def reconnect(self, force_password_renewal=False):
        if self.connection_id:
            self.rest_endpoint.reconnect(
                self.connection_id,
                force_password_renewal,
                timeout=adapter_config.default_api_timeout,
            )

    @log_entry_and_exit
    def disconnect2(self):
        if self.connection_id:
            self.rest_endpoint.disconnect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    def destroy(self):
        if self.connection_id:
            self.rest_endpoint.destroy(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)


class ConnectFromEnvironment(object):
    @log_entry_and_exit
    def connect_from_environment(self, transport):
        result = self.rest_endpoint.connect_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    def create_from_environment(self, transport):
        result = self.rest_endpoint.create_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id


class Twin(object):
    @log_entry_and_exit
    def enable_twin(self):
        return self.rest_endpoint.enable_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def get_twin(self):
        return self.rest_endpoint.get_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def patch_twin(self, patch):
        self.rest_endpoint.patch_twin(
            self.connection_id, patch, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def wait_for_desired_property_patch_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_desired_properties_patch),
            (self.connection_id,),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread


class HandleMethods(object):
    @log_entry_and_exit
    def enable_methods(self):
        return self.rest_endpoint.enable_methods(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    """
    roundtrip_method_async
    Description: This is a poorly named method. It is essentially create a
    method callback and then wait for a method call.
    """

    @log_entry_and_exit
    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        request_and_response = {
            "requestPayload": request_payload,
            "responsePayload": response_payload,
            "statusCode": status_code,
        }
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.roundtrip_method_call),
            (self.connection_id, method_name, request_and_response),
            dict(timeout=adapter_config.default_api_timeout),
        )
        return thread


class Telemetry(object):
    @log_entry_and_exit
    def send_event(self, body):
        self.rest_endpoint.send_event(
            self.connection_id, body, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def send_event_async(self, body):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.send_event),
            (self.connection_id, body),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread


class InputsAndOutputs(object):
    @log_entry_and_exit
    def send_output_event(self, output_name, body):
        self.rest_endpoint.send_output_event(
            self.connection_id,
            output_name,
            body,
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    def enable_input_messages(self):
        return self.rest_endpoint.enable_input_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    def wait_for_input_event_async(self, input_name):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_input_message),
            (self.connection_id, input_name),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread


class InvokeMethods(object):
    @log_entry_and_exit
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_module_method),
            (self.connection_id, device_id, module_id, method_invoke_parameters),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread

    @log_entry_and_exit
    def call_device_method_async(self, device_id, method_invoke_parameters):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.invoke_device_method),
            (self.connection_id, device_id, method_invoke_parameters),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread


class ConnectionStatus(object):
    @log_entry_and_exit
    def get_connection_status(self):
        return self.rest_endpoint.get_connection_status(self.connection_id)

    @log_entry_and_exit
    def wait_for_connection_status_change_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_connection_status_change),
            (self.connection_id,),
            dict(timeout=adapter_config.default_api_timeout),
        )
        time.sleep(wait_time_for_async_start)
        return thread


class C2d(object):
    @log_entry_and_exit
    def enable_c2d(self):
        self.rest_endpoint.enable_c2d_messages(self.connection_id)

    @log_entry_and_exit
    def wait_for_c2d_message_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_c2d_message),
            (self.connection_id,),
        )
        return thread


class ServiceSideOfTwin(object):
    @log_entry_and_exit
    def patch_module_twin(self, device_id, module_id, patch):
        self.rest_endpoint.patch_module_twin(
            self.connection_id,
            device_id,
            module_id,
            patch,
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    def get_device_twin(self, device_id):
        return self.rest_endpoint.get_device_twin(
            self.connection_id, device_id, timeout=adapter_config.default_api_timeout
        )

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
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).device
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()


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
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).module
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()


class RegistryApi(ServiceConnectDisconnect, ServiceSideOfTwin, AbstractRegistryApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).registry
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""

    @log_entry_and_exit
    def get_module_twin(self, device_id, module_id):
        return self.rest_endpoint.get_module_twin(
            self.connection_id,
            device_id,
            module_id,
            timeout=adapter_config.default_api_timeout,
        )


class ServiceApi(ServiceConnectDisconnect, InvokeMethods, AbstractServiceApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).service
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()
