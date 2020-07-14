# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import datetime
import threading
import contextlib
from horton_logging import logger


def null_logger(*args, **kwargs):
    pass


class NoLock(contextlib.AbstractContextManager):
    def __init__(self):
        self.thread = threading.current_thread()

    def __enter__(self):
        assert threading.current_thread() == self.thread

    def __exit__(self, *args):
        assert threading.current_thread() == self.thread


class ReportGroup(object):
    def __init__(self, name, reports, logger=logger):
        self.lock = threading.Lock()
        self.name = name
        self.reports = reports
        self.logger = logger or null_logger

    def add_sample(self, sample):
        with self.lock:
            for report in self.reports:
                report.add_sample(sample)

    def print_report(self):
        with self.lock:
            self.logger("{} reports:".format(self.name))
            self.logger("-----------")
            for report in self.reports:
                report.print_report()


class ReportAverage(object):
    def __init__(self, name, logger=logger):
        self.lock = threading.Lock()
        self.name = name
        self.logger = logger or null_logger
        self.total = 0
        self.sample_count = 0

    def add_sample(self, sample):
        with self.lock:
            self.sample_count += 1
            self.total += sample

    def get_average(self):
        with self.lock:
            return self.total / self.sample_count

    def print_report(self):
        with self.lock:
            self.logger(
                "{} average: {}".format(self.name, self.total / self.sample_count)
            )


class ReportCount(object):
    def __init__(self, name, test_function=lambda x: True, logger=logger):
        self.lock = threading.Lock()
        self.name = name
        self.test_function = test_function
        self.logger = logger or null_logger
        self.count = 0

    def add_sample(self, sample):
        with self.lock:
            if self.test_function(sample):
                self.count += 1

    def get_count(self):
        with self.lock:
            return self.count

    def print_report(self):
        with self.lock:
            self.logger("{} count: {}".format(self.name, self.count))


class ReportMax(object):
    def __init__(self, name, logger=logger):
        self.lock = threading.Lock()
        self.name = name
        self.logger = logger or null_logger
        self.max = 0

    def add_sample(self, sample):
        with self.lock:
            if sample > self.max:
                self.max = sample

    def get_max(self):
        with self.lock:
            return self.max

    def print_report(self):
        with self.lock:
            self.logger("{} max: {}".format(self.name, self.max))


class MeasureRunningCodeBlock(contextlib.AbstractContextManager):
    def __init__(self, name, reports=[], logger=logger, use_lock=True):
        self.lock = threading.Lock() if use_lock else NoLock()
        self.count = 0
        self.name = name
        self.logger = logger or null_logger
        self.at_zero = threading.Event()
        self.reports = [ReportMax(name)] + reports

    def __enter__(self):
        with self.lock:
            self.count += 1
            for report in self.reports:
                report.add_sample(self.count)
            self.logger("enter: {} count at {}".format(self.name, self.count))
            self.at_zero.clear()

    def __exit__(self, *args):
        with self.lock:
            self.count -= 1
            self.logger("exit: {} count at {}".format(self.name, self.count))
            if self.count == 0:
                self.at_zero.set()

    def wait_for_zero(self):
        self.at_zero.wait()

    def get_count(self):
        with self.lock:
            return self.count

    def get_max(self):
        with self.lock:
            return self.reports[0].get_max()

    def print_report(self):
        with self.lock:
            for report in self.reports:
                report.print_report()


class MeasureLatency(contextlib.AbstractContextManager):
    def __init__(self, tracker=None):
        self.start_time = None
        self.end_time = None
        self.tracker = tracker

    def __enter__(self):
        self.start_time = datetime.datetime.now()

    def __exit__(self, *args):
        self.end_time = datetime.datetime.now()
        if self.tracker:
            self.tracker.add_sample(self.get_latency())

    def get_latency(self):
        if self.start_time:
            if self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            else:
                return (datetime.datetime.now() - self.start_time).total_seconds()
        else:
            return 0


class TrackCount(object):
    def __init__(self, use_lock=True):
        self.lock = threading.Lock() if use_lock else NoLock()
        self.count = 0

    def increment(self):
        with self.lock:
            self.count += 1
            return self.count

    def get_count(self):
        with self.lock:
            return self.count

    def extract(self):
        with self.lock:
            count = self.count
            self.count = 0
            return count


class TrackMax(object):
    def __init__(self, use_lock=True):
        self.lock = threading.Lock() if use_lock else NoLock()
        self.max = 0

    def add_sample(self, sample):
        with self.lock:
            if sample > self.max:
                self.max = sample

    def get_max(self):
        with self.lock:
            return self.max

    def extract(self):
        with self.lock:
            max = self.max
            self.max = 0
            return max
