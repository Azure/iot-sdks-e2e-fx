# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import DictionaryObject


class LonghaulConfig(DictionaryObject):
    def __init__(self):
        super(LonghaulConfig, self).__init__()
        self.total_duration = datetime.timedelta()
        self.timeout_interval = datetime.timedelta(minutes=2)
        self.property_update_interval = datetime.timedelta(seconds=10)
        self.telenetry_interval = datetime.timedelta(seconds=10)
        self.eventhub_renew_interval = datetime.timedelta(minutes=15)
        self.d2c_enabled = False
        self.d2c_interval_length = 1
        self.d2c_ops_per_interval = 10
        self.d2c_count_failures_allowed = 0
        self.lock_attributes()


LonghaulConfig._defaults = LonghaulConfig()
