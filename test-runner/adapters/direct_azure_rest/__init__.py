#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from .direct_eventhub_api import EventHubApi, object_list as eventhub_object_list
from .direct_service_api import ServiceApi, object_list as service_object_list
from .direct_registry_api import RegistryApi, object_list as registry_object_list


def cleanup_test_objects():
    # We need to operate on a copy of the list because the disconnect
    # function modifies object_list which breaks the iteration
    list_copy = eventhub_object_list + service_object_list + registry_object_list
    for obj in list_copy:
        obj.disconnect()
