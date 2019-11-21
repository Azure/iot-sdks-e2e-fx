# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractNetApi:
    @abc.abstractmethod
    def set_destination_sync(self, ip, transport):
        pass

    @abc.abstractmethod
    def disconnect_sync(self, disconnect_type):
        pass

    @abc.abstractmethod
    def reconnect_sync(self):
        pass

    @abc.abstractmethod
    def disconnect_after_c2d_sync(self, disconnect_type):
        pass

    @abc.abstractmethod
    def disconnect_after_d2c_sync(self, disconnect_type):
        pass
