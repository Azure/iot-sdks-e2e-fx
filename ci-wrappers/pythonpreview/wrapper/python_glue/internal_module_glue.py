#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import logging
import internal_wrapper_glue
from internal_module_glue_sync import InternalModuleGlueSync
try:
    from internal_module_glue_async import InternalModuleGlueAsync
except SyntaxError:
    pass

logger = logging.getLogger(__name__)

def InternalModuleGlue():
    if internal_wrapper_glue.do_async:
        logger.info("Creating InternalModuleGlueAsync")
        return InternalModuleGlueAsync()
    else:
        logger.info("Creating InternalModuleGlueAsync")
        return InternalModuleGlueSync()
