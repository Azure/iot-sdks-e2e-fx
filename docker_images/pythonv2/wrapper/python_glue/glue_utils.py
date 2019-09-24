# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging

logger = logging.getLogger(__name__)


class ConnectEventWatcher(object):
    def _attach_connect_event_watcher(self):
        """
        Since the iothub clients don't expose on_connected and on_disconnected events,
        we have to add our own.
        """
        old_on_connected = self.client._iothub_pipeline.on_connected

        def new_on_connected():
            logger.info("new_on_connected")
            self.connected = True
            old_on_connected()

        self.client._iothub_pipeline.on_connected = new_on_connected

        old_on_disconnected = self.client._iothub_pipeline.on_disconnected

        def new_on_disconnected():
            logger.info("new_on_disconnected")
            self.connected = False
            old_on_disconnected()

        self.client._iothub_pipeline.on_disconnected = new_on_disconnected
