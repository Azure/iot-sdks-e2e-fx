#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from .direct_module_api import ModuleApi, object_list


def cleanup_test_objects():
    # We need to operate on a copy of the list because the disconnect
    # function modifies object_list which breaks the iteration
    list_copy = object_list.copy()
    for obj in list_copy:
        obj.disconnect()
