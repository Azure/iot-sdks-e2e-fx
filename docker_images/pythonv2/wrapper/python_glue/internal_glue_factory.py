# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import internal_control_glue
from internal_iothub_glue import InternalDeviceGlueSync, InternalModuleGlueSync

try:
    from internal_iothub_glue_async import (
        InternalDeviceGlueAsync,
        InternalModuleGlueAsync,
    )
    import wrap_async_in_sync
    import wrap_sync_in_async
except SyntaxError:
    pass

logger = logging.getLogger(__name__)


device = "device"
sync_device = "sync_device"
async_device = "async_device"
module = "module"
sync_module = "sync_module"
async_module = "async_module"
sync_interface = "sync_interface"
async_interface = "async_interface"

valid_object_types = [device, module]
valid_interface_types = [sync_interface, async_interface]


def create_glue_object(object_type, interface_type):
    if object_type not in valid_object_types:
        raise ValueError(
            "object_type {} invalid.  only {} are accepted".format(
                object_type, valid_object_types
            )
        )
    if interface_type not in valid_interface_types:
        raise ValueError(
            "interface_type {} invalid.  only {} are accepted".format(
                interface_type, valid_interface_types
            )
        )

    if internal_control_glue.do_async:
        object_type = "async_" + object_type
    else:
        object_type = "sync_" + object_type

    logger.info("making {} object with {}".format(object_type, interface_type))

    if object_type == sync_device:
        logger.info("Creating DeviceGlue")
        obj = InternalDeviceGlueSync()
    elif object_type == async_device:
        logger.info("Creating DeviceGlueAsync")
        obj = InternalDeviceGlueAsync()
    elif object_type == sync_module:
        logger.info("Creating ModuleGlue")
        obj = InternalModuleGlueSync()
    elif object_type == async_module:
        logger.info("Creating ModuleGlueAsync")
        obj = InternalModuleGlueAsync()

    if interface_type.startswith("async_"):
        # async glue has some sync methods (connection_status.py) that need to be wrapped,
        # so we call this for sync and async glue both
        logger.info("Wrapping sync methods in async facade")
        wrap_sync_in_async.wrap_object(obj)
    if interface_type.startswith("sync_") and object_type.startswith("async_"):
        # only wrap async in sync if we're using async glue.  sync glue doesn't have
        # any async methods.
        logger.info("Wrapping async methods in sync facade")
        wrap_async_in_sync.wrap_object(obj)

    return obj
