# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractSystemControlApi:
    @abc.abstractmethod
    def set_network_destination(self, ip, transport):
        pass

    @abc.abstractmethod
    def disconnect_network(self, disconnect_type):
        pass

    @abc.abstractmethod
    def reconnect_network(self):
        pass

    # BKTODO: schedule discussion

    @abc.abstractmethod
    def get_system_stats(self, wrapper_pid):
        pass
