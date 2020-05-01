# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import convert
import internal_control_glue
from connection_status import ConnectionStatus
from azure.iot.device import IoTHubDeviceClient, IoTHubModuleClient, MethodResponse
from azure.iot.device.common import mqtt_transport


logger = logging.getLogger(__name__)


DEFAULT_KEEPALIVE = 8


class Connect(ConnectionStatus):
    def connect_sync(self, transport_type, connection_string, cert):
        logger.info("connecting using " + transport_type)
        self.create_from_connection_string(transport_type, connection_string, cert)
        self.client.connect()

    def disconnect_sync(self):
        # disconnect destroys the object.  We will never use it again
        logger.info("disconnecting")
        self.destroy_sync()

    def create_from_connection_string_sync(
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

    def create_from_x509_sync(self, transport_type, x509):
        # BKTODO
        pass

    def connect2_sync(self):
        self.client.connect()

    def reconnect_sync(self, force_renew_password):
        # BKTODO
        pass

    def disconnect2_sync(self):
        # disconnect2 keeps the object around.  We might use it again
        self.client.disconnect()

    def destroy_sync(self):
        if self.client:
            try:
                self.client.disconnect()
            finally:
                self.client = None


class ConnectFromEnvironment(object):
    def connect_from_environment_sync(self, transport_type):
        logger.info("connecting from environment")
        self.create_from_environment(transport_type)
        self.client.connect()

    def create_from_environment_sync(self, transport_type):

        internal_control_glue.set_sas_interval()

        kwargs = {}
        if transport_type == "mqttws":
            kwargs["websockets"] = True

        self.client = self.client_class.create_from_edge_environment(**kwargs)

        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()


class HandleMethods(object):
    def enable_methods_sync(self):
        # Unnecessary, methods are enabled implicity when method operations are initiated.
        pass

    def wait_for_method_and_return_response_sync(self, methodName, requestAndResponse):
        # receive method request
        logger.info("Waiting for method request")
        request = self.client.receive_method_request(methodName)
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
        self.client.send_method_response(response)
        logger.info("Method response sent")


class Twin(object):
    def enable_twin_sync(self):
        pass

    def wait_for_desired_property_patch_sync(self):
        logger.info("Waiting for desired property patch")
        patch = self.client.receive_twin_desired_properties_patch()
        logger.info("patch received")
        logger.info(str(patch))
        return {"desired": patch}

    def get_twin_sync(self):
        logger.info("getting twin")
        twin = self.client.get_twin()
        logger.info("done getting twin")
        return twin

    def send_twin_patch_sync(self, twin):
        logger.info("setting reported property patch")
        self.client.patch_twin_reported_properties(twin.reported)
        logger.info("done setting reported properties")


class C2d(object):
    def enable_c2d_sync(self):
        # Unnecessary, C2D messages are enabled implicitly when C2D operations are initiated.
        pass

    def wait_for_c2d_message_sync(self):
        logger.info("Waiting for c2d message")
        message = self.client.receive_message()
        logger.info("Message received")
        return convert.incoming_message_to_test_script_object(message)


class Telemetry(object):
    def send_event_sync(self, event_body):
        logger.info("sending event")
        self.client.send_message(
            convert.test_script_object_to_outgoing_message(event_body)
        )
        logger.info("send confirmation received")


class InputsAndOutputs(object):
    def enable_input_messages_sync(self):
        # Unnecessary, input messages are enabled implicitly when input operations are initiated.
        pass

    def wait_for_input_message_sync(self, input_name):
        logger.info("Waiting for input message")
        message = self.client.receive_message_on_input(input_name)
        logger.info("Message received")
        logger.info(str(message))
        converted = convert.incoming_message_to_test_script_object(message)
        logger.info("Converted to:")
        logger.info(str(converted))
        logger.info("---")
        return converted

    def send_output_event_sync(self, output_name, event_body):
        logger.info("sending output event")
        self.client.send_message_to_output(
            convert.test_script_object_to_outgoing_message(event_body), output_name
        )
        logger.info("send confirmation received")


class InvokeMethods(object):
    def invoke_module_method_sync(self, device_id, module_id, method_invoke_parameters):
        logger.info("Invoking a method on the module.")
        method_response = self.client.invoke_method(
            device_id=device_id,
            module_id=module_id,
            method_params=method_invoke_parameters,
        )
        logger.info("Method Invoked and response received.")
        return method_response

    def invoke_device_method_sync(self, device_id, method_invoke_parameters):
        logger.info("Invoking a method on the module.")
        method_response = self.client.invoke_method(
            device_id=device_id, method_params=method_invoke_parameters
        )
        logger.info("Method Invoked and response received.")
        return method_response


class BlobUpload(object):
    def get_storage_info_for_blob_sync(self, blob_name):
        return self.client.get_storage_info_for_blob(blob_name)

    def notify_blob_upload_status_sync(
        self, correlation_id, is_success, status_code, status_description
    ):
        self.client.notify_blob_upload_status(
            correlation_id, is_success, status_code, status_description
        )


class InternalDeviceGlueSync(Connect, HandleMethods, C2d, Twin, Telemetry, BlobUpload):
    def __init__(self):
        self.client_class = IoTHubDeviceClient
        self.client = None


class InternalModuleGlueSync(
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
        self.client_class = IoTHubModuleClient
        self.client = None
