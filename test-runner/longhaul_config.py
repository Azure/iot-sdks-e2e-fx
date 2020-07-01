# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import SimpleObject, DictionaryObject


class Platform(SimpleObject):
    def __init__(self):
        super(Platform, self).__init__()
        self.os = ""
        self.framework_version = ""


class OpConfig(SimpleObject):
    def __init__(self):
        super(OpConfig, self).__init__()
        self.enabled = False
        self.interval = 0
        self.ops_per_interval = 0
        self.slow_send_threshold = datetime.timedelta(0)
        self.slow_send_and_receive_threshold = datetime.timedelta(0)


class TestConfig(SimpleObject):
    def __init__(self):
        super(TestConfig, self).__init__()
        self.total_duration = datetime.timedelta()
        self.stats_window_op_count = 100
        self.timeout_interval = datetime.timedelta(minutes=2)
        self.max_fail_count = 1
        self.d2c = OpConfig()


class OpStatus(SimpleObject):
    def __init__(self):
        super(OpStatus, self).__init__()
        self.ops_completed = 0
        self.ops_failed = 0
        self.ops_waiting_to_send = 0
        self.ops_waiting_to_complete = 0
        self.ops_slow_send = 0
        self.ops_slow_send_and_receive = 0
        self.mean_send_latency = 0.0
        self.mean_send_and_receive_latency = 0.0


class TestStatus(SimpleObject):
    def __init__(self):
        super(TestStatus, self).__init__()

        self.status = "new"
        self.start_time = datetime.datetime.min
        self.elapsed_time = datetime.timedelta(0)
        self.memory_used = 0.0
        self.active_objects = 0

        self.d2c = OpStatus()


class Telemetry(DictionaryObject):
    def __init__(self):
        super(Telemetry, self).__init__()
        self.op_id = 0
        self.test_status = TestStatus()
        self.lock_attributes()

    def to_dict(self, op_id):
        with self._lock:
            self.op_id = op_id
            return super(Telemetry, self).to_dict()


Telemetry._defaults = Telemetry()


class DesiredTestProperties(DictionaryObject):
    def __init__(self):
        super(DesiredTestProperties, self).__init__()
        self.test_config = TestConfig()
        self.lock_attributes()


DesiredTestProperties._defaults = DesiredTestProperties()


class ReportedTestProperties(DictionaryObject):
    def __init__(self):
        super(ReportedTestProperties, self).__init__()
        self.platform = Platform()
        self.test_config = TestConfig()
        self.test_status = TestStatus()
        self.lock_attributes()


ReportedTestProperties._defaults = ReportedTestProperties()
