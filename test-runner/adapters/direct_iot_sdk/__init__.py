#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from .direct_module_api import ModuleApi, object_list_sync
from .direct_module_api_aio import ModuleApiAsync, object_list_async
from .direct_device_api import DeviceApi, object_list_sync
from .direct_device_api_aio import DeviceApiAsync, object_list_async


def cleanup_test_objects():
    # We need to operate on a copy of the list because the disconnect
    # function modifies object_list which breaks the iteration
    list_copy = object_list_sync.copy()
    for obj in list_copy:
        obj.disconnect()
