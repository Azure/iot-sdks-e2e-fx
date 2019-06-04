# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import internal_wrapper_glue
from ..abstract_wrapper_api import AbstractWrapperApi


class WrapperApi(AbstractWrapperApi):
    def log_message(self, message):
        internal_wrapper_glue.log_message(message)

    def cleanup(self):
        pass

    def get_capabilities(self):
        return internal_wrapper_glue.get_capabilities()

    def set_flags(self, flags):
        internal_wrapper_glue.set_flags(flags)
