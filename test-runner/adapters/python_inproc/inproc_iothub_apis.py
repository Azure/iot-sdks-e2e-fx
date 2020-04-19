# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from internal_iothub_glue import InternalDeviceGlue, InternalModuleGlue
from ..abstract_iothub_apis import AbstractDeviceApi, AbstractModuleApi
from ..decorators import emulate_async

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


class Connect(object):
    def connect_sync(self, transport, connection_string, ca_certificate):
        client_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        self.glue.connect(transport, connection_string, cert)

    def disconnect_sync(self):
        if self in client_object_list:
            client_object_list.remove(self)

        if self.glue:
            self.glue.disconnect()
            self.glue = None

    def create_from_connection_string_sync(
        self, transport, connection_string, ca_certificate
    ):
        client_object_list.append(self)
        if "cert" in ca_certificate:
            cert = ca_certificate["cert"]
        else:
            cert = None
        self.glue.create_from_connection_string(transport, connection_string, cert)

    def create_from_x509_sync(self, transport, x509):
        client_object_list.append(self)
        self.glue.create_from_x509(transport, x509)

    @emulate_async
    def connect2(self):
        self.glue.connect2()

    @emulate_async
    def reconnect(self, force_password_renewal=False):
        self.glue.reconnect(force_password_renewal)

    @emulate_async
    def disconnect2(self):
        self.glue.disconnect2()

    def destroy_sync(self):
        if self in client_object_list:
            client_object_list.remove(self)

        self.glue.destroy()


class ConnectFromEnvironment(object):
    def connect_from_environment_sync(self, transport):
        client_object_list.append(self)
        self.glue.connect_from_environment(transport)

    def create_from_environment_sync(self, transport):
        client_object_list.append(self)
        self.glue.create_from_environment(transport)


class Twin(object):
    @emulate_async
    def enable_twin(self):
        self.glue.enable_twin()

    @emulate_async
    def get_twin(self):
        return self.glue.get_twin()

    @emulate_async
    def patch_twin(self, patch):
        twin = PythonDirectTwin()
        twin.reported = patch["reported"]
        self.glue.send_twin_patch(twin)

    @emulate_async
    def wait_for_desired_property_patch(self):
        return self.glue.wait_for_desired_property_patch()


class Telemetry(object):
    @emulate_async
    def send_event(self, body):
        obj = PythonDirectEventBody()
        obj.body = body
        self.glue.send_event(obj)


class C2d(object):
    @emulate_async
    def enable_c2d(self):
        self.glue.enable_c2d()

    @emulate_async
    def wait_for_c2d_message(self):
        message = self.glue.wait_for_c2d_message()
        obj = PythonDirectEventBody()
        obj.body = message["body"]
        return obj


class InputsAndOutputs(object):
    @emulate_async
    def enable_input_messages(self):
        self.glue.enable_input_messages()

    @emulate_async
    def send_output_event(self, output_name, body):
        obj = PythonDirectEventBody()
        obj.body = body
        self.glue.send_output_event(output_name, obj)

    @emulate_async
    def wait_for_input_event(self, input_name):
        message = self.glue.wait_for_input_message(input_name)
        obj = PythonDirectEventBody()
        obj.body = message["body"]
        return obj


class HandleMethods(object):
    @emulate_async
    def enable_methods(self):
        self.glue.enable_methods()

    @emulate_async
    def wait_for_method_and_return_response(
        self, method_name, status_code, request_payload, response_payload
    ):
        class RequestAndResponse(object):
            pass

        request_and_response = RequestAndResponse()
        request_and_response.request_payload = request_payload
        request_and_response.response_payload = response_payload
        request_and_response.status_code = status_code
        return self.glue.wait_for_method_and_return_response(
            method_name, request_and_response
        )


class InvokeMethods(object):
    @emulate_async
    def call_module_method(self, device_id, module_id, method_invoke_parameters):
        return self.glue.invoke_module_method(
            device_id, module_id, method_invoke_parameters
        )

    @emulate_async
    def call_device_method(self, device_id, method_invoke_parameters):
        return self.glue.invoke_device_method(device_id, method_invoke_parameters)


class ConnectionStatus(object):
    @emulate_async
    def get_connection_status(self):
        return self.glue.get_connection_status()

    @emulate_async
    def wait_for_connection_status_change(self, connection_status):
        return self.glue.wait_for_connection_status_change(connection_status)


class BlobUpload(object):
    @emulate_async
    def get_storage_info_for_blob(self, blob_name):
        return self.glue.get_storage_info_for_blob(blob_name)

    @emulate_async
    def notify_blob_upload_status(
        self, correlation_id, is_success, status_code, status_description
    ):
        return self.glue.notify_blob_upload_status(
            correlation_id, is_success, status_code, status_description
        )


class DeviceApi(
    Connect,
    Twin,
    Telemetry,
    C2d,
    HandleMethods,
    ConnectionStatus,
    BlobUpload,
    AbstractDeviceApi,
):
    def __init__(self):
        self.glue = InternalDeviceGlue()


class ModuleApi(
    Connect,
    ConnectFromEnvironment,
    Twin,
    Telemetry,
    InputsAndOutputs,
    HandleMethods,
    InvokeMethods,
    ConnectionStatus,
    AbstractModuleApi,
):
    def __init__(self):
        self.glue = InternalModuleGlue()
