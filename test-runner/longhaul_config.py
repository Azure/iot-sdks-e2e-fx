# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information
import datetime
from dictionary_object import SimpleObject, DictionaryObject


class Progress(SimpleObject):
    def __init__(self):
        self.status = "new"
        self.start_time = datetime.datetime()
        self.total_duration = datetime.datetime()
        self.elapsed_time = datetime.datetime()
        self.finish_time = datetime.datetime()
        self.memory_used = 0.0
        self.active_objects = 0
        self.completed_operations = 0
        self.outstanding_operations = 0
        self.slow_initiate_operations = 0
        self.slow_complete_operations = 0

    def update(self):
        pass


class Platform(SimpleObject):
    def __init__(self):
        self.os = ""
        self.framework_version = ""
        self.heap_size = 0.0


class Sdk(SimpleObject):
    def __init__(self):
        self.languate = ""
        self.version = ""
        self.install_source = ""
        self.source_repo = ""
        self.source_branch = ""
        self.source_pr = ""
        self.SourceCommit = ""


class FeatureConfig(SimpleObject):
    def __init__(self):
        self.enabled = False
        self.interval = 0
        self.ops_per_interval = 0


class TestConfig(SimpleObject):
    def __init__(self):
        self.scenario = ""
        self.total_duration = datetime.timedelta()
        self.d2c = FeatureConfig()


class FeatureStats(SimpleObject):
    def __init__(self):
        self.complete_operations = 0
        self.outstanding_operations = 0
        self.failed_operations = 0
        self.slow_init_operations = 0
        self.slow_complete_operations = 0


class TestStats(SimpleObject):
    def __init__(self):
        self.d2c = FeatureStats()


class Telemetry(DictionaryObject):
    def __init__(self):
        super(Telemetry, self).__init__()
        self.progress = Progress()


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
