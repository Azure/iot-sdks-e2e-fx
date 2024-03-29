# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import convert
import queue
import threading
from connection_status import ConnectionStatus
from azure.iot.device import IoTHubDeviceClient, IoTHubModuleClient, MethodResponse


logger = logging.getLogger(__name__)


DEFAULT_KEEPALIVE = 8


def get_kwargs(transport_type):
    kwargs = {}

    kwargs["keep_alive"] = DEFAULT_KEEPALIVE
    if transport_type == "mqttws":
        kwargs["websockets"] = True

    return kwargs


class Connect(ConnectionStatus):
    def connect_sync(self, transport_type, connection_string, cert):
        assert False

    def disconnect_sync(self):
        assert False

    def create_from_connection_string_sync(
        self, transport_type, connection_string, cert
    ):
        kwargs = get_kwargs(transport_type)

        if "GatewayHostName" in connection_string:
            self.client = self.client_class.create_from_connection_string(
                connection_string, server_verification_cert=cert, **kwargs
            )
        else:
            self.client = self.client_class.create_from_connection_string(
                connection_string, **kwargs
            )
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
                if hasattr(self.client, "shutdown"):
                    self.client.shutdown()
                else:
                    self.client.disconnect()
            finally:
                self.client = None


class DeviceConnect(object):
    def create_from_symmetric_key_sync(
        self, transport_type, device_id, hostname, symmetric_key
    ):
        kwargs = get_kwargs(transport_type)

        self.client = self.client_class.create_from_symmetric_key(
            symmetric_key, hostname, device_id, **kwargs
        )

        self._attach_connect_event_watcher()


class ModuleConnect(object):
    def connect_from_environment_sync(self, transport_type):
        assert False

    def create_from_environment_sync(self, transport_type):
        kwargs = get_kwargs(transport_type)

        self.client = self.client_class.create_from_edge_environment(**kwargs)

        self._attach_connect_event_watcher()

    def create_from_symmetric_key_sync(
        self, transport_type, device_id, module_id, hostname, symmetric_key
    ):
        kwargs = get_kwargs(transport_type)

        self.client = self.client_class.create_from_symmetric_key(
            symmetric_key, hostname, device_id, module_id, **kwargs
        )

        self._attach_connect_event_watcher()


class HandleMethods(object):
    def enable_methods_sync(self):
        def on_method_request_received(req):
            with self.lock:
                if req.name not in self.method_queues:
                    self.method_queues[req.name] = queue.Queue()
            self.method_queues[req.name].put(req)

        self.client.on_method_request_received = on_method_request_received

        # Python SDK 3.x needs to make an additional invocation
        if hasattr(self.client, "start_method_request_receive"):
            self.client.start_method_request_receive()

    def wait_for_method_and_return_response_sync(self, methodName, requestAndResponse):
        with self.lock:
            if methodName not in self.method_queues:
                self.method_queues[methodName] = queue.Queue()

        # receive method request
        logger.info("Waiting for method request")
        request = self.method_queues[methodName].get()
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
        def on_patch_received(patch):
            self.twin_patch_queue.put(patch)

        self.client.on_twin_desired_properties_patch_received = on_patch_received

        # Python SDK 3.x needs to make an additional invocation
        if hasattr(self.client, "start_twin_desired_properties_patch_receive"):
            self.client.start_twin_desired_properties_patch_receive()

    def wait_for_desired_property_patch_sync(self):
        logger.info("Waiting for desired property patch")
        patch = self.twin_patch_queue.get()
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
        def on_message_received(msg):
            self.c2d_queue.put(msg)

        self.client.on_message_received = on_message_received

        # Python SDK 3.x needs to make an additional invocation
        if hasattr(self.client, "start_message_receive"):
            self.client.start_message_receive()

    def wait_for_c2d_message_sync(self):
        logger.info("Waiting for c2d message")
        message = self.c2d_queue.get()
        logger.info("Message received")
        return convert.incoming_message_to_test_script_object(message)


class Telemetry(object):
    def send_event_sync(self, event_body):
        self.client.send_message(
            convert.test_script_object_to_outgoing_message(event_body)
        )


class InputsAndOutputs(object):
    def enable_input_messages_sync(self):
        def on_message_received(msg):
            with self.lock:
                if msg.input_name not in self.input_queues:
                    self.input_queues[msg.input_name] = queue.Queue()
            self.input_queues[msg.input_name].put(msg)

        self.client.on_message_received = on_message_received

        # Python SDK 3.x needs to make an additional invocation
        if hasattr(self.client, "start_message_receive"):
            self.client.start_message_receive()

    def wait_for_input_message_sync(self, input_name):
        with self.lock:
            if input_name not in self.input_queues:
                self.input_queues[input_name] = queue.Queue()

        logger.info("Waiting for input message")
        message = self.input_queues[input_name].get()
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


class InternalDeviceGlueSync(
    Connect, DeviceConnect, HandleMethods, C2d, Twin, Telemetry, BlobUpload
):
    def __init__(self):
        self.client_class = IoTHubDeviceClient
        self.client = None
        self.c2d_queue = queue.Queue()
        self.twin_patch_queue = queue.Queue()
        self.method_queues = {}
        self.lock = threading.Lock()


class InternalModuleGlueSync(
    Connect,
    ModuleConnect,
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
        self.c2d_queue = queue.Queue()
        self.twin_patch_queue = queue.Queue()
        self.method_queues = {}
        self.lock = threading.Lock()
        self.input_queues = {}
