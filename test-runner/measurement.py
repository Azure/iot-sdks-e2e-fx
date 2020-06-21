# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import datetime
import threading
import contextlib
from horton_logging import logger


class ReportGroup(object):
    def __init__(self, name, reports):
        self.lock = threading.Lock()
        self.name = name
        self.reports = reports

    def add_sample(self, sample):
        with self.lock:
            for report in self.reports:
                report.add_sample(sample)

    def print_report(self):
        with self.lock:
            logger("{} reports:".format(self.name))
            logger("-----------")
            for report in self.reports:
                report.print_report()


class ReportAverage(object):
    def __init__(self, name):
        self.lock = threading.Lock()
        self.name = name
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
            logger("{} average: {}".format(self.name, self.total / self.sample_count))


class ReportCount(object):
    def __init__(self, name, test_function=lambda x: True):
        self.lock = threading.Lock()
        self.name = name
        self.test_function = test_function
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
            logger("{} count: {}".format(self.name, self.count))


class ReportMax(object):
    def __init__(self, name):
        self.lock = threading.Lock()
        self.name = name
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
            logger("{} max: {}".format(self.name, self.max))


class MeasureRunningCodeBlock(contextlib.AbstractContextManager):
    def __init__(self, name, reports=[]):
        self.current_count = 0
        self.lock = threading.Lock()
        self.name = name
        self.at_zero = threading.Event()
        self.reports = [ReportMax(name)] + reports

    def __enter__(self):
        with self.lock:
            self.current_count += 1
            for report in self.reports:
                report.add_sample(self.current_count)
            logger("enter: {} count at {}".format(self.name, self.current_count))
            self.at_zero.clear()

    def __exit__(self, *args):
        with self.lock:
            self.current_count -= 1
            logger("exit: {} count at {}".format(self.name, self.current_count))
            if self.current_count == 0:
                self.at_zero.set()

    def wait_for_zero(self):
        self.at_zero.wait()

    def get_current_count(self):
        with self.lock:
            return self.current_count

    def get_max(self):
        with self.lock:
            return self.reports[0].get_max()

    def print_report(self):
        with self.lock:
            for report in self.reports:
                report.print_report()


class MeasureLatency(contextlib.AbstractContextManager):
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.datetime.now()

    def __exit__(self, *args):
        self.end_time = datetime.datetime.now()

    def get_latency(self):
        return (self.end_time - self.start_time).total_seconds()


class MeasureSimpleCount(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.count = 0

    def increment(self):
        with self.lock:
            self.count += 1
            return self.count

    def get_count(self):
        with self.lock:
            return self.count
