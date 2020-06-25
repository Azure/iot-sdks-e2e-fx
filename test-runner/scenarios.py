# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

scenarios = {
    "edgehub_module": ["testgroup_edgehub_module_client"],
    "iothub_module": ["testgroup_iothub_module_client"],
    "edgehub_module_fi": ["testgroup_edgehub_fault_injection"],
    "iothub_module_and_device": [
        "testgroup_iothub_module_client",
        "testgroup_iothub_device_client",
    ],
    "iothub_device": ["testgroup_iothub_device_client"],
    "iothub_module_quick_drop": ["testgroup_iothub_module_quick_drop"],
    "iothub_device_quick_drop": ["testgroup_iothub_device_quick_drop"],
    "edgehub_module_quick_drop": ["testgroup_edgehub_module_quick_drop"],
    "iothub_module_full_drop": ["testgroup_iothub_module_full_drop"],
    "iothub_device_full_drop": ["testgroup_iothub_device_full_drop"],
    "edgehub_module_full_drop": ["testgroup_edgehub_module_full_drop"],
    "edgehub_module_stress": ["testgroup_edgehub_module_stress"],
    "iothub_module_stress": ["testgroup_iothub_module_stress"],
    "iothub_device_stress": ["testgroup_iothub_device_stress"],
}
