# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import convert
import internal_control_glue
from connection_status import ConnectionStatus
from azure.iot.device import MethodResponse
from azure.iot.device.aio import IoTHubDeviceClient, IoTHubModuleClient
from azure.iot.device.common import mqtt_transport

logger = logging.getLogger(__name__)

DEFAULT_KEEPALIVE = 8


class Connect(ConnectionStatus):
    async def connect(self, transport_type, connection_string, cert):
        logger.info("connecting using " + transport_type)
        self.create_from_connection_string(transport_type, connection_string, cert)
        await self.client.connect()

    async def disconnect(self):
        logger.info("disconnecting")
        # disconnect destroys the object.  We will never use it again
        await self.destroy()

    async def create_from_connection_string(
        self, transport_type, connection_string, cert
    ):

        internal_control_glue.set_sas_interval_sync()

        kwargs = {}
        if transport_type == "mqttws":
            kwargs["websockets"] = True

        if "GatewayHostName" in connection_string:
            self.client = self.client_class.create_from_connection_string(
                connection_string, server_verification_cert=cert, **kwargs
            )
        else:
            self.client = self.client_class.create_from_connection_string(
                connection_string, **kwargs
            )
        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()

    async def create_from_x509(self, transport_type, x509):
        # BKTODO
        pass

    async def connect2(self):
        await self.client.connect()

    async def reconnect(self, force_renew_password):
        # BKTODO
        pass

    async def disconnect2(self):
        # disconnect2 keeps the object around.  We might use it again
        await self.client.disconnect()

    async def destroy(self):
        if self.client:
            try:
                await self.client.disconnect()
            finally:
                self.client = None


class ConnectFromEnvironment(object):
    async def connect_from_environment(self, transport_type):
        logger.info("connecting from environment")
        self.create_from_environment(transport_type)
        await self.client.connect()

    async def create_from_environment(self, transport_type):

        internal_control_glue.set_sas_interval()

        kwargs = {}
        if transport_type == "mqttws":
            kwargs["websockets"] = True

        self.client = IoTHubModuleClient.create_from_edge_environment(**kwargs)
        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()


class HandleMethods(object):
    async def enable_methods(self):
        # Unnecessary, methods are enabled implicity when method operations are initiated.
        pass

    async def wait_for_method_and_return_response(self, methodName, requestAndResponse):
        # receive method request
        logger.info("Waiting for method request")
        request = await self.client.receive_method_request(methodName)
        logger.info("Method request received")

        # verify name and payload
        expected_name = methodName
        expected_payload = requestAndResponse.request_payload["payload"]
        if request.name == expected_name:
            if request.payload == expected_payload:
                logger.info("Method name and payload matched. Returning response")
                resp_status = requestAndResponse.status_code
                resp_payload = requestAndResponse.response_payload
            else:
                logger.info("Request payload doesn't match")
                logger.info("expected: " + expected_payload)
                logger.info("received: " + request.payload)
                resp_status = 500
                resp_payload = None
        else:
            logger.info("Method name doesn't match")
            logger.info("expected: '" + expected_name + "'")
            logger.info("received: '" + request.name + "'")
            resp_status = 404
            resp_payload = None

        # send method response
        response = MethodResponse(
            request_id=request.request_id, status=resp_status, payload=resp_payload
        )
        await self.client.send_method_response(response)
        logger.info("Method response sent")


class Twin(object):
    async def enable_twin(self):
        pass

    async def wait_for_desired_property_patch(self):
        logger.info("Waiting for desired property patch")
        patch = await self.client.receive_twin_desired_properties_patch()
        logger.info("patch received")
        return {"desired": patch}

    async def get_twin(self):
        logger.info("getting twin")
        twin = await self.client.get_twin()
        logger.info("done getting twin")
        return twin

    async def send_twin_patch(self, props):
        logger.info("setting reported property patch")
        await self.client.patch_twin_reported_properties(props.to_dict()["reported"])
        logger.info("done setting reported properties")


class C2d(object):
    async def enable_c2d(self):
        # Unnecessary, C2D messages are enabled implicitly when C2D operations are initiated.
        pass

    async def wait_for_c2d_message(self):
        logger.info("Waiting for c2d message")
        message = await self.client.receive_message()
        logger.info("Message received")
        return convert.incoming_message_to_test_script_object(message)


class Telemetry(object):
    async def send_event(self, event_body):
        logger.info("sending event")
        await self.client.send_message(
            convert.test_script_object_to_outgoing_message(event_body)
        )
        logger.info("send confirmation received")


class InputsAndOutputs(object):
    async def enable_input_messages(self):
        # Unnecessary, input messages are enabled implicitly when input operations are initiated.
        pass

    async def wait_for_input_message(self, input_name):
        logger.info("Waiting for input message")
        message = await self.client.receive_message_on_input(input_name)
        logger.info("Message received")
        return convert.incoming_message_to_test_script_object(message)

    async def send_output_event(self, output_name, event_body):
        logger.info("sending output event")
        await self.client.send_message_to_output(
            convert.test_script_object_to_outgoing_message(event_body), output_name
        )
        logger.info("send confirmation received")


class InvokeMethods(object):
    async def invoke_module_method(
        self, device_id, module_id, method_invoke_parameters
    ):
        logger.info("Invoking a method on the module.")
        method_response = await self.client.invoke_method(
            device_id=device_id,
            module_id=module_id,
            method_params=method_invoke_parameters,
        )
        logger.info("Method Invoked and response received.")
        return method_response

    async def invoke_device_method(self, device_id, method_invoke_parameters):
        logger.info("Invoking a method on the module.")
        method_response = await self.client.invoke_method(
            device_id=device_id, method_params=method_invoke_parameters
        )
        logger.info("Method Invoked and response received.")
        return method_response


class BlobUpload(object):
    async def get_storage_info_for_blob(self, blob_name):
        info = await self.client.get_storage_info_for_blob(blob_name)
        return info

    async def notify_blob_upload_status(
        self, correlation_id, is_success, status_code, status_description
    ):
        await self.client.notify_blob_upload_status(
            correlation_id, is_success, status_code, status_description
        )


class InternalDeviceGlueAsync(Connect, HandleMethods, C2d, Telemetry, Twin, BlobUpload):
    def __init__(self):
        self.client = None
        self.client_class = IoTHubDeviceClient
        self.connected = False


class InternalModuleGlueAsync(
    Connect,
    ConnectFromEnvironment,
    HandleMethods,
    C2d,
    Twin,
    Telemetry,
    InputsAndOutputs,
    InvokeMethods,
):
    def __init__(self):
        self.client = None
        self.client_class = IoTHubModuleClient
        self.connected = False
