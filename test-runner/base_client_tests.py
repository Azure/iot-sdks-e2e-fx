# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest

from horton_logging import logger


class BaseClientTests(object):
    @pytest.mark.it("Can connect and immediately disconnect")
    async def test_client_connect_disconnect(self, client):
        if client.capabilities.v2_connect_group:
            # Retry on transient connect failures (e.g. MQTT CONNACK not
            # received within paho's keepalive window). This retry is kept
            # local to the positive connect test on purpose: putting it in
            # the generic connect2() adapter would also retry negative /
            # regression tests that expect connect to fail fast.
            last_exc = None
            for attempt in range(3):
                try:
                    await client.connect2()
                    return
                except Exception as e:
                    last_exc = e
                    logger(
                        "connect2 attempt {} failed ({}); retrying".format(
                            attempt + 1, e
                        )
                    )
                    await asyncio.sleep(5)
            raise last_exc
