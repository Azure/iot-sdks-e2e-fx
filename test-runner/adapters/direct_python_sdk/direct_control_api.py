# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import internal_control_glue
from ..abstract_control_api import AbstractControlApi
from ..decorators import emulate_async


class ControlApi(AbstractControlApi):
    def log_message_sync(self, message):
        internal_control_glue.log_message(message)

    def cleanup_sync(self):
        pass

    def get_capabilities_sync(self):
        return internal_control_glue.get_capabilities()

    def set_flags_sync(self, flags):
        internal_control_glue.set_flags(flags)
