# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import datetime
import math
import sample_content
import threading
import contextlib
from horton_logging import logger

pytestmark = pytest.mark.asyncio

# per-test-case timeout for this module
test_timeout = 900


class ExcThread(threading.Thread):
    def __init__(self, target, args=None):
        self.args = args if args else []
        self.target = target
        self.exc = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            self.target(*self.args)
        except Exception as e:
            # self.exc =sys.exc_info()
            self.exc = e


class SampleAverage(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.total = 0
        self.sample_count = 0
        self.max = 0

    def add_sample(self, sample):
        with self.lock:
            self.sample_count += 1
            self.total += sample
            if sample > self.max:
                self.max = sample

    def get_max(self):
        with self.lock:
            return self.max

    def get_average(self):
        with self.lock:
            return self.total / self.sample_count


class InstanceCounter(contextlib.AbstractContextManager):
    def __init__(self, object_type):
        self.instance_count = 0
        self.max_instances = 0
        self.lock = threading.Lock()
        self.object_type = object_type
        self.at_zero = threading.Event()

    def __enter__(self):
        with self.lock:
            self.instance_count += 1
            logger(
                "enter: {} count at {}".format(self.object_type, self.instance_count)
            )
            if self.instance_count > self.max_instances:
                self.max_instances = self.instance_count
            self.at_zero.clear()

    def __exit__(self, *args):
        with self.lock:
            self.instance_count -= 1
            logger("exit: {} count at {}".format(self.object_type, self.instance_count))
            if self.instance_count == 0:
                self.at_zero.set()

    def wait_for_zero(self):
        self.at_zero.wait()

    def get_max(self):
        with self.lock:
            return self.max_instances

    def get_count(self):
        with self.lock:
            return self.instance_count


class LatencyMeasurement(contextlib.AbstractContextManager):
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = datetime.datetime.now()

    def __exit__(self, *args):
        self.end_time = datetime.datetime.now()

    def get_latency(self):
        return (self.end_time - self.start_time).total_seconds()


class PerfTest(object):
    async def test_throughput(self, client):
        count = 2500

        payloads = [sample_content.make_message_payload() for x in range(0, count)]

        start_time = datetime.datetime.now()
        await asyncio.gather(*[client.send_event(payload) for payload in payloads])
        duration = (datetime.datetime.now() - start_time).total_seconds()

        mps = math.floor(count / duration)

        logger(
            "{} messages were sent in {} seconds for {} messages/second".format(
                count, duration, mps
            )
        )

    async def do_test_multithreaded(
        self, client, events_per, duration, max_threads=None, max_latency=None
    ):
        threads = []

        message_counter = InstanceCounter("Message")
        thread_counter = InstanceCounter("Thread")
        average_latency = SampleAverage()

        async def send_single():
            latency = LatencyMeasurement()
            with message_counter:
                with latency:
                    logger("start send")
                    await client.send_event(sample_content.make_message_payload())
                    logger("end send")
            average_latency.add_sample(latency.get_latency())
            if max_latency and latency.get_latency() > max_latency:
                raise Exception(
                    "max latency exceeded: {}".format(latency.get_latency())
                )

        def threadproc():
            with thread_counter:

                if max_threads and thread_counter.get_count() > max_threads:
                    raise Exception(
                        "thread limit exceeded: {}".format(thread_counter.get_count())
                    )

                async def main():
                    results = await asyncio.gather(
                        *[send_single() for i in range(0, events_per)]
                    )

                    for result in results:
                        if isinstance(result, Exception):
                            raise result

                asyncio.run(main())

        for i in range(0, duration):
            t = ExcThread(target=threadproc)
            t.start()
            threads.append(t)

            await asyncio.sleep(1)

            old_threads = threads
            threads = []
            for t in old_threads:
                if t.isAlive():
                    threads.append(t)
                elif t.exc:
                    raise (t.exc)

        logger(
            "events_per = {} messages left = {}".format(
                events_per, message_counter.get_count()
            )
        )

        thread_counter.wait_for_zero()

        logger("{} threads max".format(thread_counter.get_max()))
        logger("Average latency {} seconds".format(average_latency.get_average()))
        logger("Max latency {} seconds".format(average_latency.get_max()))

        return thread_counter.get_max(), average_latency.get_average()

    @pytest.mark.timeout(7300)
    async def test_perf_longhaul(self, client):
        duration = 7200
        events_per = 20
        max_threads = 20
        max_latency = 60

        threads, latency = await self.do_test_multithreaded(
            client, events_per, duration, max_threads, max_latency
        )

        logger("FINAL RESULT:")
        logger(
            "Sent {} events per second for {} seconds with max {} threads".format(
                events_per, duration, threads
            )
        )

    async def test_multithreaded(self, client):
        duration = 30
        first = 1
        last = 60
        biggest_success = 0
        smallest_failure = last + 1
        found = False
        results = []

        try:
            while first <= last and not found:
                midpoint = (first + last) // 2
                logger("running with {} events per batch".format(midpoint))
                threads, latency = await self.do_test_multithreaded(
                    client, midpoint, duration
                )
                results.append(
                    {"evens_per": midpoint, "max_threads": threads, "latency": latency}
                )
                if threads != 1:
                    logger(
                        "FAILED with {} events per second ({},{})".format(
                            midpoint, threads, latency
                        )
                    )
                    assert midpoint < smallest_failure
                    smallest_failure = midpoint
                else:
                    logger(
                        "SUCCEEDED with {} events per second ({},{})".format(
                            midpoint, threads, latency
                        )
                    )
                    assert midpoint > biggest_success
                    biggest_success = midpoint
                if biggest_success + 1 >= smallest_failure:
                    found = True
                else:
                    if threads > 1:
                        last = midpoint - 1
                    else:
                        first = midpoint + 1

        finally:
            logger("FINAL RESULT:")
            logger("biggest_success = {} events per second".format(biggest_success))
            logger("smallest_failure = {} events per second".format(smallest_failure))
            logger("INDIVIDUAL RESULTS:")
            for res in results:
                logger(res)


@pytest.mark.testgroup_edgehub_module_2h_stress
@pytest.mark.testgroup_iothub_module_2h_stress
@pytest.mark.describe("Module Client Perf")
@pytest.mark.timeout(test_timeout)
class TestModuleClientPerf(PerfTest):
    @pytest.fixture
    def client(self, test_module):
        return test_module


@pytest.mark.testgroup_iothub_device_2h_stress
@pytest.mark.describe("Device Client Perf")
@pytest.mark.timeout(test_timeout)
class TestDeviceClientPerf(PerfTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device
