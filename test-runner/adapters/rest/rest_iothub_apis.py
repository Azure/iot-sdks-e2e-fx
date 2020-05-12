# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
import time
from .generated.e2erestapi import AzureIOTEndToEndTestWrapperRestApi as GeneratedSyncApi
from .generated.e2erestapi.aio import (
    AzureIOTEndToEndTestWrapperRestApi as GeneratedAsyncApi,
)
from .generated.e2erestapi.models import MethodInvoke, EventBody
from .. import adapter_config
from .rest_decorators import log_entry_and_exit
from ..abstract_iothub_apis import (
    AbstractDeviceApi,
    AbstractModuleApi,
    AbstractServiceApi,
    AbstractRegistryApi,
)


class ServiceConnectDisconnect(object):
    @log_entry_and_exit(print_args=False)
    async def connect(self, connection_string):
        result = await self.rest_endpoint.connect(
            connection_string, timeout=adapter_config.default_api_timeout
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    async def disconnect(self):
        if self.connection_id:
            await self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""


class Connect(object):
    @log_entry_and_exit(print_args=False)
    async def connect(self, transport, connection_string, ca_certificate):
        result = await self.rest_endpoint.connect(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        self.connection_id = result.connection_id

    @log_entry_and_exit
    async def disconnect(self):
        if self.connection_id:
            await self.rest_endpoint.disconnect(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit(print_args=False)
    async def create_from_connection_string(
        self, transport, connection_string, ca_certificate
    ):
        result = await self.rest_endpoint.create_from_connection_string(
            transport,
            connection_string,
            ca_certificate=ca_certificate,
            timeout=adapter_config.default_api_timeout,
        )
        assert not self.connection_id
        self.connection_id = result.connection_id

    @log_entry_and_exit(print_args=False)
    async def create_from_x509(self, transport, x509):
        result = await self.rest_endpoint.create_from_x509(
            transport, x509, timeout=adapter_config.default_api_timeout
        )
        assert not self.connection_id
        self.connection_id = result.connection_id

    @log_entry_and_exit
    async def connect2(self):
        if self.connection_id:
            await self.rest_endpoint.connect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )

    @log_entry_and_exit
    async def reconnect(self, force_password_renewal=False):
        if self.connection_id:
            await self.rest_endpoint.reconnect(
                self.connection_id,
                force_password_renewal,
                timeout=adapter_config.default_api_timeout,
            )

    @log_entry_and_exit
    async def disconnect2(self):
        if self.connection_id:
            await self.rest_endpoint.disconnect2(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)

    @log_entry_and_exit
    async def destroy(self):
        if self.connection_id:
            await self.rest_endpoint.destroy(
                self.connection_id, timeout=adapter_config.default_api_timeout
            )
            self.connection_id = ""
            # give edgeHub a chance to disconnect MessagingServiceClient from IoTHub.  It does this lazily after the module disconnects from edgeHub
            time.sleep(2)


class ConnectFromEnvironment(object):
    @log_entry_and_exit
    async def connect_from_environment(self, transport):
        result = await self.rest_endpoint.connect_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        assert not self.connection_id
        self.connection_id = result.connection_id

    @log_entry_and_exit
    async def create_from_environment(self, transport):
        result = await self.rest_endpoint.create_from_environment(
            transport, timeout=adapter_config.default_api_timeout
        )
        assert not self.connection_id
        self.connection_id = result.connection_id


class Twin(object):
    @log_entry_and_exit
    async def enable_twin(self):
        return await self.rest_endpoint.enable_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    async def get_twin(self):
        twin = await self.rest_endpoint.get_twin(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )
        return twin.as_dict()

    @log_entry_and_exit
    async def patch_twin(self, patch):
        await self.rest_endpoint.patch_twin(
            self.connection_id, patch, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    async def wait_for_desired_property_patch(self):
        patch = await self.rest_endpoint.wait_for_desired_properties_patch(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )
        return patch.as_dict()


class HandleMethods(object):
    @log_entry_and_exit
    async def enable_methods(self):
        return await self.rest_endpoint.enable_methods(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    """
    wait_for_method_and_return_response
    Description: This is a poorly named method. It is essentially create a
    method callback and then wait for a method call.
    """

    @log_entry_and_exit
    async def wait_for_method_and_return_response(
        self, method_name, status_code, request_payload, response_payload
    ):
        request_and_response = {
            "requestPayload": request_payload,
            "responsePayload": response_payload,
            "statusCode": status_code,
        }
        return await self.rest_endpoint.wait_for_method_and_return_response(
            self.connection_id,
            method_name,
            request_and_response,
            timeout=adapter_config.default_api_timeout,
        )


class Telemetry(object):
    @log_entry_and_exit
    async def send_event(self, body):
        await self.rest_endpoint.send_event(
            self.connection_id,
            EventBody(body=body),
            timeout=adapter_config.default_api_timeout,
        )


class InputsAndOutputs(object):
    @log_entry_and_exit
    async def send_output_event(self, output_name, body):
        await self.rest_endpoint.send_output_event(
            self.connection_id,
            output_name,
            EventBody(body=body),
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    async def enable_input_messages(self):
        return await self.rest_endpoint.enable_input_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    async def wait_for_input_event(self, input_name):
        return await self.rest_endpoint.wait_for_input_message(
            self.connection_id, input_name, timeout=adapter_config.default_api_timeout
        )


class InvokeMethods(object):
    @log_entry_and_exit
    async def call_module_method(self, device_id, module_id, method_invoke_parameters):
        method_invoke = MethodInvoke(
            method_name=method_invoke_parameters["methodName"],
            payload=method_invoke_parameters["payload"],
            response_timeout_in_seconds=method_invoke_parameters[
                "responseTimeoutInSeconds"
            ],
            connect_timeout_in_seconds=method_invoke_parameters[
                "connectTimeoutInSeconds"
            ],
        )
        return await self.rest_endpoint.invoke_module_method(
            self.connection_id,
            device_id,
            module_id,
            method_invoke,
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    async def call_device_method(self, device_id, method_invoke_parameters):
        method_invoke = MethodInvoke(
            method_name=method_invoke_parameters["methodName"],
            payload=method_invoke_parameters["payload"],
            response_timeout_in_seconds=method_invoke_parameters[
                "responseTimeoutInSeconds"
            ],
            connect_timeout_in_seconds=method_invoke_parameters[
                "connectTimeoutInSeconds"
            ],
        )
        return await self.rest_endpoint.invoke_device_method(
            self.connection_id,
            device_id,
            method_invoke,
            timeout=adapter_config.default_api_timeout,
        )


class ConnectionStatus(object):
    @log_entry_and_exit
    async def get_connection_status(self):
        status = await self.rest_endpoint.get_connection_status(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )
        try:
            return json.loads(status)
        except ValueError:
            return status

    @log_entry_and_exit
    async def wait_for_connection_status_change(self, connection_status):
        status = await self.rest_endpoint.wait_for_connection_status_change(
            self.connection_id,
            connection_status,
            timeout=adapter_config.default_api_timeout,
        )
        try:
            return json.loads(status)
        except ValueError:
            return status


class C2d(object):
    @log_entry_and_exit
    async def enable_c2d(self):
        await self.rest_endpoint.enable_c2d_messages(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )

    @log_entry_and_exit
    async def wait_for_c2d_message(self):
        return await self.rest_endpoint.wait_for_c2d_message(
            self.connection_id, timeout=adapter_config.default_api_timeout
        )


class ServiceSideOfTwin(object):
    @log_entry_and_exit
    async def get_module_twin(self, device_id, module_id):
        twin = await self.rest_endpoint.get_module_twin(
            self.connection_id,
            device_id,
            module_id,
            timeout=adapter_config.default_api_timeout,
        )
        return twin.as_dict()

    @log_entry_and_exit
    async def patch_module_twin(self, device_id, module_id, patch):
        await self.rest_endpoint.patch_module_twin(
            self.connection_id,
            device_id,
            module_id,
            patch,
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    async def get_device_twin(self, device_id):
        twin = await self.rest_endpoint.get_device_twin(
            self.connection_id, device_id, timeout=adapter_config.default_api_timeout
        )
        return twin.as_dict()

    @log_entry_and_exit
    async def patch_device_twin(self, device_id, patch):
        await self.rest_endpoint.patch_device_twin(
            self.connection_id,
            device_id,
            patch,
            timeout=adapter_config.default_api_timeout,
        )


class BlobUpload(object):
    @log_entry_and_exit
    async def get_storage_info_for_blob(self, blob_name):
        return await self.rest_endpoint.get_storage_info_for_blob(
            self.connection_id, blob_name
        )

    @log_entry_and_exit
    async def notify_blob_upload_status(
        self, correlation_id, is_success, status_code, status_description
    ):
        await self.rest_endpoint.notify_blob_upload_status(
            self.connection_id,
            correlation_id,
            is_success,
            status_code,
            status_description,
        )


class DeviceApi(
    Connect,
    C2d,
    Telemetry,
    Twin,
    HandleMethods,
    ConnectionStatus,
    BlobUpload,
    AbstractDeviceApi,
):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).device
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
        self.rest_endpoint = GeneratedAsyncApi(hostname).module
        self.rest_endpoint.config.retry_policy.retries = 0

        self.connection_id = ""


class RegistryApi(ServiceConnectDisconnect, ServiceSideOfTwin, AbstractRegistryApi):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).registry
        self.rest_endpoint.config.retry_policy.retries = 0

        self.connection_id = ""


class ServiceApi(ServiceConnectDisconnect, InvokeMethods, AbstractServiceApi):
    def __init__(self, hostname):
        self.rest_endpoint = GeneratedAsyncApi(hostname).service
        self.rest_endpoint.config.retry_policy.retries = 0

        self.connection_id = ""

    @log_entry_and_exit
    async def send_c2d(self, device_id, event_body):
        await self.rest_endpoint.send_c2d(
            self.connection_id,
            device_id,
            EventBody(body=event_body),
            timeout=adapter_config.default_api_timeout,
        )

    @log_entry_and_exit
    async def get_blob_upload_status(self):
        raise NotImplementedError()
