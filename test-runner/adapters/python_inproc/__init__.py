# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from .inproc_iothub_apis import ModuleApi, DeviceApi, client_object_list
from .inproc_control_api import ControlApi


def cleanup_test_objects():
    # We need to operate on a copy of the list because the disconnect
    # function modifies object_list which breaks the iteration
    list_copy = client_object_list.copy()
    for obj in list_copy:
        obj.disconnect_sync()
