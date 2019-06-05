#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import time
from rest_wrappers.generated.e2erestapi.azure_iot_end_to_end_test_wrapper_rest_api import (
    AzureIOTEndToEndTestWrapperRestApi,
)
from multiprocessing.pool import ThreadPool
from ..decorators import log_entry_and_exit
from .. import adapter_config
from ..abstract_device_api import AbstractDeviceApi
from .base_module_or_device_api import BaseModuleOrDeviceApi

# Amount of time to wait after submitting async request.  Gives server time to call API before calling the next API.
wait_time_for_async_start = 1


class DeviceApi(BaseModuleOrDeviceApi, AbstractDeviceApi):
    def __init__(self, hostname):
        self.rest_endpoint = AzureIOTEndToEndTestWrapperRestApi(hostname).device
        self.rest_endpoint.config.retry_policy.retries = 0
        self.connection_id = ""
        self.pool = ThreadPool()

    def __del__(self):
        self.pool.close()
        # Do not join.  If any threads hang, this thread will hang and we'll never exit pytest.
        # self.pool.join()

    @log_entry_and_exit
    def enable_c2d(self):
        self.rest_endpoint.enable_c2d_messages(self.connection_id)

    @log_entry_and_exit
    def wait_for_c2d_message_async(self):
        thread = self.pool.apply_async(
            log_entry_and_exit(self.rest_endpoint.wait_for_c2d_message),
            (self.connection_id,),
        )
        return thread
