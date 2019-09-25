# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractWrapperApi:
    @abc.abstractmethod
    def log_message_sync(self, message):
        pass

    @abc.abstractmethod
    def cleanup_sync(self):
        pass

    @abc.abstractmethod
    def get_capabilities_sync(self):
        pass

    @abc.abstractmethod
    def set_flags_sync(self, flags):
        pass

    @abc.abstractmethod
    def network_disconnect(self, disconnection_type):
        pass

    @abc.abstractmethod
    def network_reconnect(self):
        pass

    @abc.abstractmethod
    def network_reconnect_sync(self):
        pass
