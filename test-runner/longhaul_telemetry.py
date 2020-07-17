# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import DictionaryObject


class PlatformProperties(DictionaryObject):
    def __init__(self):
        self.os = ""
        self.os_release = ""
        self.system_architecture = ""
        self.language = ""
        self.language_version = ""
        self.sdk_repo = ""
        self.sdk_commit = ""
        self.sdk_sha = ""
        self.lock_attributes()


PlatformProperties._defaults = PlatformProperties()


class ExecutionProperties(DictionaryObject):
    def __init__(self):
        super(ExecutionProperties, self).__init__()
        self.execution_status = "new"
        self.execution_start_time = datetime.datetime.min
        self.execution_elapsed_time = datetime.timedelta(0)
        self.lock_attributes()


class ExecutionTelemetry(DictionaryObject):
    def __init__(self):
        super(ExecutionTelemetry, self).__init__()

        self.system_uptime_in_seconds = 0.0
        self.system_memory_size_in_kb = 0
        self.system_memory_free_in_kb = 0
        self.system_memory_available_in_kb = 0

        self.process_gc_object_count = 0
        self.process_virtual_memory_size_in_kb = 0
        self.process_resident_memory_in_kb = 0
        self.process_shared_memory_in_kb = 0
        self.process_voluntary_context_switches_per_second = 0
        self.process_nonvoluntary_contexxt_switches_per_second = 0

        self.pytest_gc_object_count = 0
        self.lock_attributes()


ExecutionTelemetry._defaults = ExecutionTelemetry()


class D2cTelemetry(DictionaryObject):
    def __init__(self):
        super(D2cTelemetry, self).__init__()
        self.total_count_d2c_completed = 0
        self.total_count_d2c_failed = 0
        self.current_count_d2c_sending = 0
        self.current_count_d2c_verifying = 0
        self.average_latency_d2c_send = 0
        self.average_latency_d2c_verify = 0
        self.lock_attributes()


D2cTelemetry.__defaults = D2cTelemetry()
