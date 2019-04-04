#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import internal_wrapper_glue
from internal_device_glue_sync import InternalDeviceGlueSync
from internal_device_glue_async import InternalDeviceGlueAsync

logger = logging.getLogger(__name__)


def InternalDeviceGlue():
    if internal_wrapper_glue.do_async:
        logger.info("Creating InternalDeviceGlueAsync")
        return InternalDeviceGlueAsync()
    else:
        logger.info("Creating InternalDeviceGluesync")
        return InternalDeviceGlueSync()
