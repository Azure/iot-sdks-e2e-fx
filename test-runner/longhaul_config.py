# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
import gc
from dictionary_object import SimpleObject, DictionaryObject


class Progress(SimpleObject):
    def __init__(self):
        super(Progress, self).__init__()

        self.index = 0
        self.status = "new"
        self.start_time = datetime.datetime()
        self.total_duration = datetime.datetime()
        self.elapsed_time = datetime.datetime()
        self.finish_time = datetime.datetime()
        self.memory_used = 0.0
        self.active_objects = 0
        self.ops_completed = 0
        self.ops_in_progress = 0
        self.ops_waiting_to_initiate = 0
        self.ops_waiting_to_complete = 0
        self.slow_initiate_ops = 0
        self.slow_complete_ops = 0

    def update(
        self,
        ops_completed=None,
        ops_in_progress=None,
        ops_waiting_to_initiate=None,
        ops_waiting_to_complete=None,
    ):
        with self._lock:

            now = datetime.datetime.now()
            if self.start_time == datetime.datetime():
                self.start_time = now
                self.finish_time = now + self.total_duration
            self.elapsed_time = now - self.start_time

            # BKTODO: this returns the gc info for the pytest process.  move this to the process under test
            counts = gc.get_counts()
            self.active_objects = counts[0] + counts[1] + counts[2]

            if ops_completed is not None:
                self.ops_completed = ops_completed
            if ops_in_progress is not None:
                self.ops_in_progress = ops_in_progress
            if ops_waiting_to_initiate is not None:
                self.ops_waiting_to_initiate = ops_waiting_to_initiate
            if ops_waiting_to_complete is not None:
                self.ops_waiting_to_complete = ops_waiting_to_complete

    def to_dict(self):
        with self._lock:
            self.index += 1
            return super(Progress, self).to_dict()


class Platform(SimpleObject):
    def __init__(self):
        super(Platform, self).__init__()
        self.os = ""
        self.framework_version = ""
        self.heap_size = 0.0


class Sdk(SimpleObject):
    def __init__(self):
        super(Sdk, self).__init__()
        self.languate = ""
        self.version = ""
        self.install_source = ""
        self.source_repo = ""
        self.source_branch = ""
        self.source_pr = ""
        self.SourceCommit = ""


class FeatureConfig(SimpleObject):
    def __init__(self):
        super(FeatureConfig, self).__init__()
        self.enabled = False
        self.interval = 0
        self.ops_per_interval = 0


class TestConfig(SimpleObject):
    def __init__(self):
        super(TestConfig, self).__init__()
        self.scenario = ""
        self.total_duration = datetime.timedelta()
        self.d2c = FeatureConfig()


class FeatureStats(SimpleObject):
    def __init__(self):
        super(FeatureStats, self).__init__()
        self.complete_ops = 0
        self.outstanding_ops = 0
        self.failed_ops = 0
        self.slow_init_ops = 0
        self.slow_complete_ops = 0


class TestStats(SimpleObject):
    def __init__(self):
        super(TestStats, self).__init__()
        self.d2c = FeatureStats()


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
        self.sdk = Sdk()
        self.test_config = TestConfig()
        self.test_stats = TestStats()


ReportedTestProperties._defaults = ReportedTestProperties()
