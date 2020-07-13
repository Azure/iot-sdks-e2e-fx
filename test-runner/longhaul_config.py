# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import DictionaryObject


class TestConfig(DictionaryObject):
    def __init__(self):
        super(TestConfig, self).__init__()
        self.test_run_total_duration = datetime.timedelta()
        self.test_run_operation_timeout_interval = datetime.timedelta(minutes=2)
        self.test_run_property_update_interval = datetime.timedelta(seconds=10)
        self.test_run_telemetry_interval = datetime.timedelta(seconds=10)
        self.test_run_eventhub_renew_interval = datetime.timedelta(minutes=15)
        self.d2c_enabled = False
        self.d2c_interval_length = 1
        self.d2c_ops_per_interval = 10
        self.d2c_count_failures_allowed = 0
        self.lock_attributes()


TestConfig._defaults = TestConfig()
