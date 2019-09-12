# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractServiceApi:
    @abc.abstractmethod
    def connect(self, connection_string):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def call_module_method_async(self, device_id, module_id, method_invoke_parameters):
        pass

    @abc.abstractmethod
    def call_device_method_async(self, device_id, method_invoke_parameters):
        pass
