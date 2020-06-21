# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import datetime
import math
import sample_content
from horton_logging import logger
from measurement import (
    MeasureRunningCodeBlock,
    MeasureLatency,
    ReportAverage,
    ReportCount,
    ReportMax,
    ReportGroup,
)
from exc_thread import ExcThread

pytestmark = pytest.mark.asyncio

# per-test-case timeout for this module
test_timeout = 900


class PerfTest(object):
    async def test_perf_simple_throughput(self, client):
        """
        Send a large number of messsages all at once and measure how many messages
        can be sent per second.  This can be used to establish a theoretical maximum for
        our library, though the number of messages per second reported by this function
        is higher than typical because of burst effects.
        """
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

        # Arbitrary goal based on experimental evidence.  The goal of this assert is to
        # flag gigantic performance drops.  Experimentally, 46 is typical.  For this assert,
        # even 30 would be acceptable
        assert mps > 40

    async def do_test_perf_send_event(
        self, client, events_per, duration, max_threads=None, max_latency=None
    ):
        """
        Helper function to send a huge quantity of events at a regular cadence
        (x messages every second) to ensure that the library can keep up with demand.
        """
        threads = []

        # these two ContextManager objects are used to measure current and maximum
        # outstanding messages and running threads.
        message_counter = MeasureRunningCodeBlock(name="message")
        thread_counter = MeasureRunningCodeBlock(name="thread")
        # This object is used to measure send_event latency and report on a number
        # of metrics.
        latency_reports = ReportGroup(
            "latency",
            reports=[
                ReportAverage("send_event latency"),
                ReportMax("send_event latency"),
                ReportCount("send_event latency > 1s", lambda x: x >= 1),
                ReportCount("send_event latency > 5s", lambda x: x >= 5),
            ],
        )

        async def send_single():
            """
            Send a single event with latency measurement.  Fail if the latency is too high.
            """
            with message_counter:
                latency = MeasureLatency()
                with latency:
                    logger("start send")
                    await client.send_event(sample_content.make_message_payload())
                    logger("end send")
                latency_reports.add_sample(latency.get_latency())
            if max_latency and latency.get_latency() > max_latency:
                raise Exception(
                    "max latency exceeded: {}".format(latency.get_latency())
                )

        def threadproc():
            """
            Thread that gets spun up once per second.  It sends x events in parallel
            and fails if any of those send_event operations fail.
            """
            with thread_counter:
                if max_threads and thread_counter.get_current_count() > max_threads:
                    raise Exception(
                        "thread limit exceeded: {}".format(
                            thread_counter.get_current_count()
                        )
                    )

                async def send_and_gather():
                    """
                    Send x events.  If any of those operations  fail, raise an exception.
                    """
                    results = await asyncio.gather(
                        *[send_single() for i in range(0, events_per)]
                    )

                    for result in results:
                        if isinstance(result, Exception):
                            raise result

                asyncio.run(send_and_gather())

        def prune_thread_list():
            # After spinning up each new thread, we go through all the old threads and see if
            # they're done.  If one is done and it fails, we raise the exception.  If one is
            # done and it does not fail, we remove it from our list of "active threads"
            nonlocal threads
            old_threads = threads
            threads = []
            for t in old_threads:
                if t.isAlive():
                    threads.append(t)
                elif t.exc:
                    raise (t.exc)

        for i in range(0, duration):
            # This is our main loop.  We spin up a new thread once per second.  We use ExcThread
            # instead of threading.Thread because we need to know if anything in our thread
            # raised an exception
            t = ExcThread(target=threadproc)
            t.start()
            threads.append(t)

            await asyncio.sleep(1)

            prune_thread_list()

        logger(
            "Done sending.  Waiting for all events to finish sending.  outstanding events = {}".format(
                message_counter.get_current_count()
            )
        )

        # Just because we finished spinning up all our threads, it doesn't mean we're done.
        # we have to wait for our threads to all finish.
        thread_counter.wait_for_zero()
        prune_thread_list()
        assert len(threads) == 0

        thread_counter.print_report()
        message_counter.print_report()
        latency_reports.print_report()

        return (thread_counter.get_max(), message_counter.get_max())

    @pytest.mark.timeout(7300)
    async def test_perf_send_event_longhaul(self, client):
        """
        Run a linghaul test to validate that send_event can keep up with a consistent
        and regular cadence of events.  This tests an arbitrary time period, with an arbitrary
        number of messages sent every second and it verifies two things:

        1. The send_event latency doesn't go too high
        2. The maximum number of running threads doesn't go too high.

        Both of these factors can indicae a slowdown in sending.

        The choice for events_per_second is arbitray baased on the results from
        test_perf_measure_send_event_capacity.  That test indicates that we can maintain
        21 messages-per-second for 30 seconds, so this test choses 15 messages per second
        but runs it for 2 hours.
        """

        duration = 7200
        events_per = 15
        max_threads = 5
        max_latency = 11

        threads = await self.do_test_perf_send_event(
            client, events_per, duration, max_threads, max_latency
        )

        logger("FINAL RESULT:")
        logger(
            "Sent {} events per second for {} seconds with max {} threads".format(
                events_per, duration, threads
            )
        )

    async def test_perf_measure_send_event_capacity(self, client):
        """
        Test for a theoretical maximum messages-per-second cadence that the library
        can maintain.  This test only runs for a short time (30 seconds right now), so
        the actual maximum cadence will likely be slower when tested over long periods.
        """
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
                threads, events = await self.do_test_perf_send_event(
                    client, midpoint, duration
                )
                results.append(
                    {
                        "evens_per": midpoint,
                        "max_threads": threads,
                        "max_events": events,
                    }
                )
                if threads != 1:
                    logger(
                        "FAILED with {} events per second (threads={}, events={})".format(
                            midpoint, threads, events
                        )
                    )
                    assert midpoint < smallest_failure
                    smallest_failure = midpoint
                else:
                    logger(
                        "SUCCEEDED with {} events per second (threads={}, events={})".format(
                            midpoint, threads, events
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
