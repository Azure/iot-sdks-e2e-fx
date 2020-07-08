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
        self.interval_length = 0
        self.ops_per_interval = 0


class TestConfig(SimpleObject):
    def __init__(self):
        super(TestConfig, self).__init__()
        self.total_duration = datetime.timedelta()
        self.timeout_interval = datetime.timedelta(minutes=5)
        self.reporting_interval = datetime.timedelta(seconds=10)
        self.telemetry_interval = datetime.timedelta(seconds=2)
        self.eventhub_renew_interval = datetime.timedelta(minutes=15)
        self.max_allowed_failures = 0
        self.d2c = OpConfig()


class OpStatus(SimpleObject):
    def __init__(self):
        super(OpStatus, self).__init__()
        self.ops_completed = 0
        self.ops_failed = 0
        self.ops_sending = 0
        self.ops_verifying = 0
        self.max_send_latency = 0
        self.max_verify_latency = 0


class TestStatus(SimpleObject):
    def __init__(self):
        super(TestStatus, self).__init__()

        self.status = "new"
        self.start_time = datetime.datetime.min
        self.elapsed_time = datetime.timedelta(0)
        self.total_ops_failed = 0

        self.d2c = OpStatus()


class IntervalReport(DictionaryObject):
    def __init__(self):
        super(IntervalReport, self).__init__()
        self.interval_id = 0
        self.objects_in_pytest_process = 0
        self.d2c = OpStatus()
        self.lock_attributes()


IntervalReport._defaults = IntervalReport()


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
