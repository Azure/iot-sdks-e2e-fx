# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import adapters
from horton_settings import settings


def logger(*args, **kwargs):
    return adapters.adapter_config.logger(*args, **kwargs)


def set_logger():
    # BKTODO: output to more than test_module
    # BKTODO: change test_module_wrapper_api to test_module_control_api
    settings.test_module.wrapper_api = adapters.create_adapter(
        settings.test_module.adapter_address, "wrapper"
    )

    def print_and_log(message):
        if settings.test_module.adapter_address != "python_inproc":
            print("PYTEST: " + message)
        settings.test_module.wrapper_api.log_message_sync(message)

    adapters.adapter_config.logger_function = print_and_log
