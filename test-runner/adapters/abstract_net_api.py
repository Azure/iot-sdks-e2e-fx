# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractNetApi:
    @abc.abstractmethod
    def set_destination(self, ip, transport):
        pass

    @abc.abstractmethod
    def disconnect(self, disconnect_type):
        pass

    @abc.abstractmethod
    def reconnect(self):
        pass

    # BKTODO: rename net control to system control?
    # BKTODO: schedule discussion

    @abc.abstractmethod
    def get_system_stats(self, wrapper_pid):
        pass
