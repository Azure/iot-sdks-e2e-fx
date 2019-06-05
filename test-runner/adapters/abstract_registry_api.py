#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import six
import abc


@six.add_metaclass(abc.ABCMeta)
class AbstractRegistryApi:
    @abc.abstractmethod
    def connect(self, connection_string):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def get_module_twin(self, device_id, module_id):
        pass

    @abc.abstractmethod
    def patch_module_twin(self, device_id, module_id, patch):
        pass

    @abc.abstractmethod
    def get_device_twin(self, device_id):
        pass

    @abc.abstractmethod
    def patch_device_twin(self, device_id, patch):
        pass
