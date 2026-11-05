# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import abc


class AbstractControlApi(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def log_message_sync(self, message):
        pass

    @abc.abstractmethod
    def get_capabilities_sync(self):
        pass

    @abc.abstractmethod
    def set_flags_sync(self, flags):
        pass

    @abc.abstractmethod
    def send_command_sync(self, message):
        pass

    @abc.abstractmethod
    def cleanup(self):
        pass

    @abc.abstractmethod
    def get_wrapper_stats(self):
        pass
