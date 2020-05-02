# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import logging
import os
import sys
from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC
from time import time
from uuid import uuid4
from .. import adapter_config
from urllib.parse import quote, quote_plus, urlencode
from connection_string import connection_string_to_dictionary, generate_auth_token

import uamqp
from uamqp import utils, errors

logger = logging.getLogger(__name__)


def _build_iothub_amqp_endpoint(config):
    hub_name = config["HostName"].split(".")[0]
    endpoint = "{}@sas.root.{}".format(config["SharedAccessKeyName"], hub_name)
    endpoint = quote_plus(endpoint)
    sas_token = generate_auth_token(
        config["HostName"],
        config["SharedAccessKeyName"],
        config["SharedAccessKey"] + "=",
    )
    endpoint = endpoint + ":{}@{}".format(quote_plus(sas_token), config["HostName"])
    return endpoint


class AmqpServiceClient:
    async def connect(self, service_connection_string):
        self.config = connection_string_to_dictionary(service_connection_string)
        self.endpoint = _build_iothub_amqp_endpoint(self.config)

        send_operation = "/messages/devicebound"
        send_target = "amqps://" + self.endpoint + send_operation
        logger.info("send target: {}".format(send_target))
        self.send_client = uamqp.async_ops.client_async.SendClientAsync(
            send_target, debug=True
        )

        self.blob_status_receive_client = None
        self.blob_status_receive_iter = None

        adapter_config.logger("AMQP service client connected")

    async def disconnect(self):
        if self.send_client:
            await self.send_client.close_async()
            self.send_client = None
            adapter_config.logger("AMQP send client disconnected")

        if self.blob_status_receive_client:
            await self.blob_status_receive_client.close_async()
            self.blob_status_receive_client = None
            adapter_config.logger("AMQP blob status receive client disconnected")

    async def send_to_device(self, device_id, message):
        msg_content = message
        app_properties = {}
        msg_props = uamqp.message.MessageProperties()
        msg_props.to = "/devices/{}/messages/devicebound".format(device_id)
        msg_props.message_id = str(uuid4())
        message = uamqp.Message(
            msg_content, properties=msg_props, application_properties=app_properties
        )
        await self.send_client.send_message_async(message)
        adapter_config.logger("AMQP service client sent: {}".format(message))

    async def get_next_blob_status(self):
        if not self.blob_status_receive_client:
            blob_status_receive_operation = "/messages/serviceBound/filenotifications"
            blob_status_receive_source = (
                "amqps://" + self.endpoint + blob_status_receive_operation
            )

            logger.info(
                "blob status receive source: {}".format(blob_status_receive_source)
            )

            self.blob_status_receive_client = uamqp.async_ops.client_async.ReceiveClientAsync(
                blob_status_receive_source
            )
            self.blob_status_receive_iter = (
                self.blob_status_receive_client.receive_messages_iter_async()
            )

        async for message in self.blob_status_receive_iter:
            return message
