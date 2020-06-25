# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import datetime
import threading
import contextlib
import statistics
import collections
from horton_logging import logger


def null_logger(*args, **kwargs):
    pass


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


Stats = collections.namedtuple("stats", "mean fiftieth_percentile slow")


class GatherStatistics(object):
    def __init__(self, name, slowness_threshold=None):
        self.lock = threading.Lock()
        self.name = name
        self.slowness_threshold = slowness_threshold
        self.slow = 0
        self.samples = []

    def add_sample(self, sample):
        with self.lock:
            self.samples.append(sample)
            if sample > self.slowness_threshold:
                self.slow += 1

    def get_stats(self):
        with self.lock:
            if len(self.samples):
                self.samples.sort()
                mean = statistics.mean(self.samples)
                fiftieth_percentile = statistics.median_grouped(
                    self.samples, interval=0.01
                )
                return Stats(
                    mean=mean, fiftieth_percentile=fiftieth_percentile, slow=self.slow
                )
            else:
                return Stats(mean=0.0, fiftieth_percentile=0.0, slow=0.0)


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
    def __init__(self, name, reports=[], logger=logger):
        self.count = 0
        self.lock = threading.Lock()
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
