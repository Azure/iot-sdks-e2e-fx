# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import datetime
import threading
import contextlib


class MeasureRunningCodeBlock(contextlib.AbstractContextManager):
    def __init__(self, name):
        self.count = 0
        self.name = name
        self.at_zero = threading.Event()

    def __enter__(self):
        self.count += 1
        self.at_zero.clear()

    def __exit__(self, *args):
        self.count -= 1
        if self.count == 0:
            self.at_zero.set()

    def wait_for_zero(self):
        self.at_zero.wait()

    def get_count(self):
        return self.count


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
    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count

    def get_count(self):
        return self.count

    def extract(self):
        count = self.count
        self.reset()
        return count


class TrackAverage(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.total = 0

    def add_sample(self, sample):
        self.total += sample
        self.count += 1

    def get_average(self):
        if self.count:
            return self.total / self.count
        else:
            return 0

    def extract(self):
        average = self.get_average()
        self.reset()
        return average
