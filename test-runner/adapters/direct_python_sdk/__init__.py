#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from .direct_module_api import ModuleApi, module_object_list
from .direct_device_api import DeviceApi, device_object_list
from .direct_wrapper_api import WrapperApi


def cleanup_test_objects():
    # We need to operate on a copy of the list because the disconnect
    # function modifies object_list which breaks the iteration
    for list in [module_object_list, device_object_list]:
        list_copy = list.copy()
        for obj in list_copy:
            obj.disconnect()
