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

try:
    from urllib import quote, quote_plus, urlencode  # Py2
except Exception:
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
    def connect(self, service_connection_string):
        self.config = connection_string_to_dictionary(service_connection_string)
        self.endpoint = _build_iothub_amqp_endpoint(self.config)
        operation = "/messages/devicebound"
        target = "amqps://" + self.endpoint + operation
        logger.info("Target: {}".format(target))
        self.send_client = uamqp.SendClient(target, debug=True)

    def disconnect(self):
        if self.send_client:
            self.send_client.close()
            self.send_client = None

    def send_to_device(self, device_id, message):
        msg_content = message
        app_properties = {}
        msg_props = uamqp.message.MessageProperties()
        msg_props.to = "/devices/{}/messages/devicebound".format(device_id)
        msg_props.message_id = str(uuid4())
        message = uamqp.Message(
            msg_content, properties=msg_props, application_properties=app_properties
        )
        self.send_client.queue_message(message)
        results = self.send_client.send_all_messages()
        assert not [m for m in results if m == uamqp.constants.MessageState.SendFailed]
        logger.info("Message sent.")
