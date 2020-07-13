# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from internal_glue_factory import create_glue_object
from ..abstract_iothub_apis import AbstractDeviceApi, AbstractModuleApi

client_object_list = []


# from EventBody
class PythonDirectEventBody(object):
    def __init__(self):
        self.body = None
        self.horton_flags = None
        self.attributes = None


# from Twin
class PythonDirectTwin(object):
    def __init__(self):
        self.reported = None
        self.desired = None

    def to_dict(self):
        return {"reported": self.reported, "desired": self.desired}


class PythonDirectBlobInfo(object):
    def __init__(self, dikt=None):
        if not dikt:
            dikt = {}
        self.additional_properties = dikt.get("additionalPoperties", {})
        self.blob_name = dikt.get("blobName", "")
        self.container_name = dikt.get("containerName", "")
        self.correlation_id = dikt.get("correlationId", "")
        self.host_name = dikt.get("hostName", "")
        self.sas_token = dikt.get("sasToken", "")


class Connect(object):
    async def connect(self, transport, connection_string, ca_certificate):
        client_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        await self.glue.connect(transport, connection_string, cert)

    async def disconnect(self):
        if self in client_object_list:
            client_object_list.remove(self)

        if self.glue:
            await self.glue.disconnect()
            self.glue = None

    async def create_from_connection_string(
        self, transport, connection_string, ca_certificate
    ):
        client_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        await self.glue.create_from_connection_string(
            transport, connection_string, cert
        )

    async def create_from_x509(self, transport, x509):
        client_object_list.append(self)
        await self.glue.create_from_x509(transport, x509)

    async def connect2(self):
        await self.glue.connect2()

    async def reconnect(self, force_password_renewal=False):
        await self.glue.reconnect(force_password_renewal)

    async def disconnect2(self):
        await self.glue.disconnect2()

    async def destroy(self):
        if self in client_object_list:
            client_object_list.remove(self)

        await self.glue.destroy()


class DeviceConnect(object):
    async def create_from_symmetric_key(
        self, transport, device_id, hostname, symmetric_key
    ):
        client_object_list.append(self)
        await self.glue.create_from_symmetric_key(
            transport, device_id, hostname, symmetric_key
        )


class ModuleConnect(object):
    async def connect_from_environment(self, transport):
        client_object_list.append(self)
        await self.glue.connect_from_environment(transport)

    async def create_from_environment(self, transport):
        client_object_list.append(self)
        await self.glue.create_from_environment(transport)

    async def create_from_symmetric_key(
        self, transport, device_id, module_id, hostname, symmetric_key
    ):
        client_object_list.append(self)
        await self.glue.create_from_symmetric_key(
            transport, device_id, module_id, hostname, symmetric_key
        )


class Twin(object):
    async def enable_twin(self):
        await self.glue.enable_twin()

    async def get_twin(self):
        return await self.glue.get_twin()

    async def patch_twin(self, patch):
        twin = PythonDirectTwin()
        twin.reported = patch["reported"]
        await self.glue.send_twin_patch(twin)

    async def wait_for_desired_property_patch(self):
        return await self.glue.wait_for_desired_property_patch()


class Telemetry(object):
    async def send_event(self, body):
        obj = PythonDirectEventBody()
        obj.body = body
        await self.glue.send_event(obj)


class C2d(object):
    async def enable_c2d(self):
        await self.glue.enable_c2d()

    async def wait_for_c2d_message(self):
        message = await self.glue.wait_for_c2d_message()
        obj = PythonDirectEventBody()
        obj.body = message["body"]
        return obj


class InputsAndOutputs(object):
    async def enable_input_messages(self):
        await self.glue.enable_input_messages()

    async def send_output_event(self, output_name, body):
        obj = PythonDirectEventBody()
        obj.body = body
        await self.glue.send_output_event(output_name, obj)

    async def wait_for_input_event(self, input_name):
        message = await self.glue.wait_for_input_message(input_name)
        obj = PythonDirectEventBody()
        obj.body = message["body"]
        return obj


class HandleMethods(object):
    async def enable_methods(self):
        await self.glue.enable_methods()

    async def wait_for_method_and_return_response(
        self, method_name, status_code, request_payload, response_payload
    ):
        class RequestAndResponse(object):
            pass

        request_and_response = RequestAndResponse()
        request_and_response.request_payload = request_payload
        request_and_response.response_payload = response_payload
        request_and_response.status_code = status_code
        return await self.glue.wait_for_method_and_return_response(
            method_name, request_and_response
        )


class InvokeMethods(object):
    async def call_module_method(self, device_id, module_id, method_invoke_parameters):
        return await self.glue.invoke_module_method(
            device_id, module_id, method_invoke_parameters
        )

    async def call_device_method(self, device_id, method_invoke_parameters):
        return await self.glue.invoke_device_method(device_id, method_invoke_parameters)


class ConnectionStatus(object):
    async def get_connection_status(self):
        return await self.glue.get_connection_status()

    async def wait_for_connection_status_change(self, connection_status):
        return await self.glue.wait_for_connection_status_change(connection_status)


class BlobUpload(object):
    async def get_storage_info_for_blob(self, blob_name):
        info = await self.glue.get_storage_info_for_blob(blob_name)
        return PythonDirectBlobInfo(info)

    async def notify_blob_upload_status(
        self, correlation_id, is_success, status_code, status_description
    ):
        await self.glue.notify_blob_upload_status(
            correlation_id, is_success, status_code, status_description
        )


class DeviceApi(
    Connect,
    DeviceConnect,
    Twin,
    Telemetry,
    C2d,
    HandleMethods,
    ConnectionStatus,
    BlobUpload,
    AbstractDeviceApi,
):
    def __init__(self):
        self.glue = create_glue_object("device", "async_interface")


class ModuleApi(
    Connect,
    ModuleConnect,
    Twin,
    Telemetry,
    InputsAndOutputs,
    HandleMethods,
    InvokeMethods,
    ConnectionStatus,
    AbstractModuleApi,
):
    def __init__(self):
        self.glue = create_glue_object("module", "async_interface")
