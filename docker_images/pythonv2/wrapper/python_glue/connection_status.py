# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
from threading import Event

logger = logging.getLogger(__name__)


class ConnectionStatus(object):
    def get_pipeline(self):
        try:
            return self.client._mqtt_pipeline
        except AttributeError:
            return self.client._iothub_pipeline

    def _attach_connect_event_watcher(self):
        """
        Since the iothub clients don't expose on_connected and on_disconnected events,
        we have to add our own.
        """
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()

        old_on_connected = self.get_pipeline().on_connected

        def new_on_connected():
            logger.info("new_on_connected")
            self.connected = True
            self.connected_event.set()
            old_on_connected()

        self.get_pipeline().on_connected = new_on_connected

        old_on_disconnected = self.get_pipeline().on_disconnected

        def new_on_disconnected():
            logger.info("new_on_disconnected")
            self.connected = False
            self.disconnected_event.set()
            old_on_disconnected()

        self.get_pipeline().on_disconnected = new_on_disconnected

    def get_connection_status(self):
        if self.connected:
            return "connected"
        else:
            return "disconnected"

    def wait_for_connection_status_change(self, connection_status):
        if self.get_connection_status() == connection_status:
            logger.info("Client is alredy {}.  Returning.".format(connection_status))
            return connection_status

        if self.connected:
            logger.info("Client appears connected.  Waiting for client to disconenct")
            self.disconnected_event.clear()
            self.disconnected_event.wait()
            logger.info("client is disconnected.  completing.")
        else:
            logger.info("Client appears disconnected.  Waiting for client to conenct")
            self.connected_event.clear()
            self.connected_event.wait()
            logger.info("client is connected.  completing.")
        return self.get_connection_status()
