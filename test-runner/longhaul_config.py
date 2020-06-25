# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
import gc
from dictionary_object import SimpleObject, DictionaryObject


class OpStats(SimpleObject):
    def __init__(self):
        super(OpStats, self).__init__()
        self.ops_completed = 0
        self.ops_failed = 0
        self.ops_waiting_to_send = 0
        self.ops_waiting_to_complete = 0
        self.ops_slow_send = 0
        self.ops_slow_send_and_receive = 0
        self.mean_send_latency = 0.0
        self.fiftieth_percentile_send_latency = 0.0
        self.mean_send_and_receive_latency = 0.0
        self.fiftieth_percentile_send_and_receive_latency = 0.0


class Progress(OpStats):
    def __init__(self):
        super(Progress, self).__init__()

        self.index = 0
        self.status = "new"
        self.start_time = datetime.datetime.min
        self.total_duration = datetime.timedelta(0)
        self.elapsed_time = datetime.timedelta(0)
        self.memory_used = 0.0
        self.active_objects = 0

    def update(self,):
        with self._lock:
            now = datetime.datetime.now()
            if self.start_time == datetime.datetime.min:
                self.start_time = now
            self.elapsed_time = now - self.start_time

            # BKTODO: this returns the gc info for the pytest process.  move this to the process under test
            counts = gc.get_count()
            self.active_objects = counts[0] + counts[1] + counts[2]

    def to_dict(self):
        with self._lock:
            self.index += 1
            return super(Progress, self).to_dict()


class Platform(SimpleObject):
    def __init__(self):
        super(Platform, self).__init__()
        self.os = ""
        self.framework_version = ""


class FeatureConfig(SimpleObject):
    def __init__(self):
        super(FeatureConfig, self).__init__()
        self.enabled = False
        self.interval = 0
        self.ops_per_interval = 0
        self.slow_send_threshold = datetime.timedelta(0)
        self.slow_send_and_receive_threshold = datetime.timedelta(0)
        self.max_slow_send_allowed = 0
        self.max_slow_send_and_receive_allowed = 0
        self.max_fail_allowed = 0


class TestConfig(SimpleObject):
    def __init__(self):
        super(TestConfig, self).__init__()
        self.scenario = ""
        self.total_duration = datetime.timedelta()
        self.d2c = FeatureConfig()


class TestStats(SimpleObject):
    def __init__(self):
        super(TestStats, self).__init__()
        self.d2c = OpStats()


class Telemetry(DictionaryObject):
    def __init__(self):
        super(Telemetry, self).__init__()
        self.horton_mid = 0
        self.progress = Progress()

    def to_dict(self, horton_mid):
        with self._lock:
            self.horton_mid = horton_mid
            return super(Telemetry, self).to_dict()


Telemetry._defaults = Telemetry()


class DesiredTestProperties(DictionaryObject):
    def __init__(self):
        super(DesiredTestProperties, self).__init__()
        self.test_config = TestConfig()


DesiredTestProperties._defaults = DesiredTestProperties()


class ReportedTestProperties(DictionaryObject):
    def __init__(self):
        super(ReportedTestProperties, self).__init__()
        self.platform = Platform()
        self.test_config = TestConfig()
        self.test_stats = TestStats()
        self.progress = Progress()


ReportedTestProperties._defaults = ReportedTestProperties()
