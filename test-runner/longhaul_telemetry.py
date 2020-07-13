# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import DictionaryObject


class PlatformProperties(DictionaryObject):
    def __init__(self):
        self.os = ""

        self.horton_repo = ""
        self.horton_branch = ""
        self.horton_uri = ""

        self.sdk_repo = ""
        self.sdk_branch = ""
        self.sdk_uri = ""
        self.lock_attributes()


PlatformProperties._defaults = PlatformProperties()


class ExecutionProperties(DictionaryObject):
    def __init__(self):
        super(ExecutionProperties, self).__init__()
        self.execution_status = "new"
        self.execution_start_time = datetime.datetime.min
        self.execution_elapsed_time = datetime.timedelta(0)
        self.lock_attributes()


class PlatformTelemetry(DictionaryObject):
    def __init__(self):
        super(PlatformTelemetry, self).__init__()
        self.procinfo_ram_total = 0
        self.procinfo_ram_used = 0
        self.procinfo_ram_free = 0
        self.system_uptime = 0
        self.user_time = 0
        self.system_time = 0
        self.lock_attributes()


PlatformTelemetry._defaults = PlatformTelemetry()


class ExecutionTelemetry(DictionaryObject):
    def __init__(self):
        super(ExecutionTelemetry, self).__init__()
        self.pytest_gc_object_count = 0
        self.sdk_gc_object_count = 0
        self.lock_attributes()


ExecutionTelemetry._defaults = ExecutionTelemetry()


class D2cTelemetry(DictionaryObject):
    def __init__(self):
        super(D2cTelemetry, self).__init__()
        self.count_total_d2c_completed = 0
        self.count_total_d2c_failed = 0
        self.count_current_d2c_sending = 0
        self.count_current_d2c_verifying = 0
        self.latency_d2c_send = 0
        self.latency_d2c_verify = 0
        self.lock_attributes()


D2cTelemetry.__defaults = D2cTelemetry()
