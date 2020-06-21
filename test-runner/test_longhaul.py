# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import json
import threading
from longhaul_config import DesiredTestProperties, Telemetry
from measurement import MeasureSimpleCount, MeasureRunningCodeBlock
from horton_logging import logger

pytestmark = pytest.mark.asyncio


desired_node_config = {
    "test_config": {
        "d2c": {"enabled": True, "interval": 1, "ops_per_interval": 5},
        "scenario": "test_longhaul_d2c_simple",
        "total_duration": "1:00:00",
    }
}


class TestOpD2c(object):
    def __init__(self, client, eventhub):
        self.client = client
        self.eventhub = eventhub

        self.telemetry = Telemetry()

        self.measure_in_progress = MeasureRunningCodeBlock()
        self.measure_initiating = MeasureRunningCodeBlock()
        self.measure_completing = MeasureRunningCodeBlock()
        self.measure_completed = MeasureSimpleCount()
        self.next_message_id = MeasureSimpleCount()

        self.mid_list = {}
        self.mid_list_lock = threading.Lock()
        self.listener = None

    async def run_one_op(self):
        with self.measure_in_progres:
            mid = self.next_message_id.increment()

            with self.measure_initiating:
                self.telemetry.progress.update(
                    completed_ops=self.measure_completed.get_count(),
                    in_progress=self.measure_in_progress.get_count(),
                    ops_waiting_to_initiate=self.measure_initiating.get_count(),
                    ops_waiting_to_complete=self.measure_completing.get_count(),
                )

                await self.client.send_event(json.dumps(self.telemetry.to_dict(mid)))

            with self.measure_completing:
                self.wait_for_completion(mid)

            self.measure_completed.increment()

    async def listen_on_eventhub(self):
        message = await self.eventhub.wait_for_next_event(self.client.device_id)
        logger("received message on eventhub  class = ".format(type(message)))

        if isinstance(message, dict) and "horton_mid" in message:
            mid = message["horton_mid"]
            with self.mid_list_lock:
                if mid in self.mid_list:
                    self.mid_list[mid].set_result(True)
                else:
                    self.mid_list[mid] = True

    async def wait_for_completion(self, mid):
        message_received = asyncio.Future()

        with self.mid_list_lock:
            # if we've received it, return.  Else, set a future for the listener to complete when it does receive.
            if mid in self.mid_list:
                del self.mid_list[mid]
                return
            else:
                self.mid_list[mid] = message_received

            # see if the previous listener is done.
            if self.listener and self.listener.done:
                # call result() to force an exception if the listener had one
                self.listener.result()
                self.listener = None

            # start a new future
            if self.listener is None:
                self.listener = asyncio.create_task(self.listen_on_eventhub())


class LongHaulTest(object):
    async def test_longhaul(self, client):
        test_config = DesiredTestProperties.from_dict(desired_node_config).test_config


@pytest.mark.testgroup_iothub_device_2h_stress
@pytest.mark.describe("Device Client Long Run")
class TestDeviceClientLongHaul(LongHaulTest):
    @pytest.fixture
    def client(self, test_device):
        return test_device
