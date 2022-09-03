# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import convert
from connection_status import ConnectionStatus
from azure.iot.device import MethodResponse
from azure.iot.device.aio import IoTHubDeviceClient, IoTHubModuleClient
from azure.iot.device.common import mqtt_transport
from internal_iothub_glue import get_kwargs
import asyncio
import threading


logger = logging.getLogger(__name__)

DEFAULT_KEEPALIVE = 8


class Connect(ConnectionStatus):
    async def connect(self, transport_type, connection_string, cert):
        assert False

    async def disconnect(self):
        assert False

    async def create_from_connection_string(
        self, transport_type, connection_string, cert
    ):
        self.event_loop = asyncio.get_event_loop()
        kwargs = get_kwargs(transport_type)

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
                if hasattr(self.client, "shutdown"):
                    await self.client.shutdown()
                else:
                    await self.client.disconnect()
            finally:
                self.client = None


class DeviceConnect(object):
    async def create_from_symmetric_key(
        self, transport_type, device_id, hostname, symmetric_key
    ):
        self.event_loop = asyncio.get_event_loop()
        kwargs = get_kwargs(transport_type)

        self.client = self.client_class.create_from_symmetric_key(
            symmetric_key, hostname, device_id, **kwargs
        )

        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()


class ModuleConnect(object):
    async def connect_from_environment(self, transport_type):
        assert False

    async def create_from_environment(self, transport_type):
        self.event_loop = asyncio.get_event_loop()
        kwargs = get_kwargs(transport_type)

        self.client = IoTHubModuleClient.create_from_edge_environment(**kwargs)
        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()

    async def create_from_symmetric_key(
        self, transport_type, device_id, module_id, hostname, symmetric_key
    ):
        self.event_loop = asyncio.get_event_loop()
        kwargs = get_kwargs(transport_type)

        self.client = self.client_class.create_from_symmetric_key(
            symmetric_key, hostname, device_id, module_id, **kwargs
        )

        mqtt_transport.DEFAULT_KEEPALIVE = DEFAULT_KEEPALIVE
        self._attach_connect_event_watcher()


class HandleMethods(object):
    async def enable_methods(self):
        def on_method_request_received(req):
            async def handle():
                with self.lock:
                    if req.name not in self.method_queues:
                        self.method_queues[req.name] = asyncio.Queue()

                await self.method_queues[req.name].put(req)

            return asyncio.run_coroutine_threadsafe(handle(), self.event_loop)

        self.client.on_method_request_received = on_method_request_received

    async def wait_for_method_and_return_response(self, methodName, requestAndResponse):
        with self.lock:
            if methodName not in self.method_queues:
                self.method_queues[methodName] = asyncio.Queue()

        # receive method request
        logger.info("Waiting for method request")
        request = await self.method_queues[methodName].get()
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
        def on_patch_received(patch):
            async def handle():
                await self.twin_patch_queue.put(patch)

            return asyncio.run_coroutine_threadsafe(handle(), self.event_loop)

        self.client.on_twin_desired_properties_patch_received = on_patch_received

    async def wait_for_desired_property_patch(self):
        logger.info("Waiting for desired property patch")
        patch = await self.twin_patch_queue.get()
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
        def on_message_received(msg):
            async def handle():
                await self.c2d_queue.put(msg)

            return asyncio.run_coroutine_threadsafe(handle(), self.event_loop)

        self.client.on_message_received = on_message_received

    async def wait_for_c2d_message(self):
        logger.info("Waiting for c2d message")
        message = await self.c2d_queue.get()
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
        def on_message_received(msg):
            async def handle():
                with self.lock:
                    if msg.input_name not in self.input_queues:
                        self.input_queues[msg.input_name] = asyncio.Queue()

                await self.input_queues[msg.input_name].put(msg)

            return asyncio.run_coroutine_threadsafe(handle(), self.event_loop)

        self.client.on_message_received = on_message_received

    async def wait_for_input_message(self, input_name):
        with self.lock:
            if input_name not in self.input_queues:
                self.input_queues[input_name] = asyncio.Queue()

        logger.info("Waiting for input message")
        message = await self.input_queues[input_name].get()
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


class InternalDeviceGlueAsync(
    Connect, DeviceConnect, HandleMethods, C2d, Telemetry, Twin, BlobUpload
):
    def __init__(self):
        self.client = None
        self.client_class = IoTHubDeviceClient
        self.connected = False
        self.c2d_queue = asyncio.Queue()
        self.twin_patch_queue = asyncio.Queue()
        self.method_queues = {}
        self.lock = threading.Lock()
        self.event_loop = None


class InternalModuleGlueAsync(
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
        self.client = None
        self.client_class = IoTHubModuleClient
        self.connected = False
        self.c2d_queue = asyncio.Queue()
        self.twin_patch_queue = asyncio.Queue()
        self.method_queues = {}
        self.lock = threading.Lock()
        self.input_queues = {}
        self.event_loop = None
