# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import sample_content
import limitations
from horton_logging import logger
from utilities import connect2_with_retry, twin_op_with_retry

# Amount of time to wait after updating desired properties.
wait_time_for_desired_property_updates = 5


async def patch_desired_props(registry, client, twin):
    if getattr(client, "module_id", None):
        await registry.patch_module_twin(client.device_id, client.module_id, twin)
    else:
        await registry.patch_device_twin(client.device_id, twin)


async def wait_for_reported_properties_update(*, properties_sent, client, registry):
    """
    Helper function which uses the registry to wait for reported properties
    to update to the expected value
    """
    max_retries = 30
    for retry_count in range(max_retries):
        if getattr(client, "module_id", None):
            twin_received = await registry.get_module_twin(
                client.device_id, client.module_id
            )
        else:
            twin_received = await registry.get_device_twin(client.device_id)

        reported_properties_received = twin_received["reported"]
        if "$version" in reported_properties_received:
            del reported_properties_received["$version"]
        if "$metadata" in reported_properties_received:
            del reported_properties_received["$metadata"]
        logger("expected:" + str(properties_sent["reported"]))
        logger("received:" + str(reported_properties_received))

        if properties_sent["reported"] == reported_properties_received:
            # test passed
            return
        else:
            logger("Twin does not match.  Sleeping for 2 seconds and retrying ({}/{}).".format(
                retry_count + 1, max_retries))
            await asyncio.sleep(2)

    assert False, "Reported properties did not match after {} retries".format(max_retries)


async def wait_for_desired_properties_patch(*, client, expected_twin, mistakes=1):
    mistakes_left = mistakes
    while True:
        patch_received = await client.wait_for_desired_property_patch()
        logger("desired properties sent:     " + str(expected_twin["desired"]["foo"]))

        logger("desired properties received: " + str(patch_received["desired"]["foo"]))

        if expected_twin["desired"]["foo"] == patch_received["desired"]["foo"]:
            logger("success")
            return
        else:
            if mistakes_left:
                # We sometimes get the old value before we get the new value, and that's
                # perfectly valid (especially with QOS 1 on MQTT).  If we got the wrong
                # value, we just try again.
                mistakes_left = mistakes_left - 1
                logger(
                    "trying again.  We still have {} mistakes left".format(
                        mistakes_left
                    )
                )
            else:
                logger("too many mistakes.  Failing")
                assert False


class TwinTests(object):
    @pytest.mark.it("Can connect, enable twin, and disconnect")
    async def test_client_connect_enable_twin_disconnect(self, client):
        if limitations.needs_manual_connect(client):
            await connect2_with_retry(client)
        await client.enable_twin()

    @pytest.mark.it("Can get the most recent twin from the service")
    async def test_twin_desired_props(self, client, registry):
        if limitations.needs_manual_connect(client):
            await connect2_with_retry(client)

        twin_sent = sample_content.make_desired_props()

        await patch_desired_props(registry, client, twin_sent)

        # BKTODO: Node needs this sleep to pass MQTT against edgeHub
        await asyncio.sleep(5)
        await client.enable_twin()

        max_retries = 12

        # get_twin can fail outright when edgeHub does not answer it, rather than returning a twin
        # that has not caught up yet. Those two situations need different budgets. Staleness is
        # cheap to poll for and gets the full 12 iterations. An outright failure is not cheap,
        # because each one can occupy the wrapper's REST timeout before it even returns, so letting
        # all 12 iterations absorb failures would let a sustained edgeHub non-response hold this
        # test open for far longer than the retry bound used everywhere else. Outright failures get
        # their own small budget, and the last one is re-raised rather than swallowed.
        failures_allowed = 3

        for retry_count in range(max_retries):
            try:
                twin_received = await client.get_twin()
            except Exception as e:
                failures_allowed -= 1
                if not failures_allowed:
                    logger("get_twin failed ({}). No attempts left, failing the test.".format(e))
                    raise
                logger("get_twin failed ({}). Sleeping for 5 seconds and retrying ({} attempts left).".format(
                    e, failures_allowed))
                await asyncio.sleep(5)
                continue

            logger("twin sent:    " + str(twin_sent))
            logger("twin received:" + str(twin_received))
            try:
                if twin_sent["desired"]["foo"] == twin_received["desired"]["foo"]:
                    # test passed
                    return
            except KeyError:
                logger("Twin 'desired.foo' key not present yet.")
            logger("Twin does not match.  Sleeping for 5 seconds and retrying ({}/{}).".format(
                retry_count + 1, max_retries))
            await asyncio.sleep(5)

        assert False, "Twin desired properties did not match after {} retries".format(max_retries)

    @pytest.mark.it("Can receive desired property patches as events")
    async def test_twin_desired_props_patch(self, client, registry):
        if limitations.needs_manual_connect(client):
            await connect2_with_retry(client)

        await client.enable_twin()

        # Actively verify that the twin subscription path through EdgeHub's
        # cloud proxy is fully established before starting to test desired
        # property patches.  During test setup, EdgeHub's cloud proxy can
        # be rapidly recycled, leaving SetupDesiredPropertyUpdatesAsync in
        # a retry loop that takes 45+ seconds to complete.  A successful
        # get_twin() round-trip confirms the twin channel is live, so that
        # subsequent desired property patches will be delivered.
        logger("warm-up: verifying twin channel with get_twin")
        await twin_op_with_retry(client.get_twin, "warm-up get_twin")
        logger("warm-up: twin channel is ready")

        for i in range(1, 4):
            twin_sent = sample_content.make_desired_props()

            # A single long-poll wait_for_desired_property_patch is kept alive
            # for the whole patch.  Cancelling it would orphan a wrapper-side
            # handler thread that then swallows the next patch from the queue.
            # Because that long-poll is bounded by default_api_timeout (150s),
            # the entire send/recover schedule below must stay under 150s.
            #
            # Recovery strategy when a patch does not arrive:
            #   - A successful get_twin() only proves the module<->EdgeHub twin
            #     channel.  Desired-property *delivery* additionally requires
            #     EdgeHub's cloud-side MessagingServiceClient to finish setting
            #     up its upstream subscription, which can legitimately take
            #     ~45s.  So the first attempt waits the longest to give a
            #     merely-slow proxy time to come online.
            #   - If that long wait still yields nothing, the cloud proxy is
            #     wedged rather than slow.  Re-issuing enable_twin from the
            #     module is a no-op once the twin feature is enabled, so it
            #     cannot help.  Instead we disconnect/reconnect the module:
            #     EdgeHub tears the MessagingServiceClient down on disconnect
            #     (lazily) and rebuilds it on reconnect, giving the upstream
            #     desired-property subscription a fresh start.  connection_id is
            #     preserved across disconnect2/connect2, so the pending
            #     long-poll keeps reading from the same queue.
            wait_schedule = [45, 30, 30]  # 105s of waits + 2 reconnects < 150s

            logger("start waiting for patch {}".format(i))
            patch_future = asyncio.ensure_future(
                wait_for_desired_properties_patch(
                    client=client, expected_twin=twin_sent
                )
            )
            await asyncio.sleep(3)  # wait for async call to take effect

            for attempt, wait_interval in enumerate(wait_schedule):
                if attempt > 0:
                    # Patch was not delivered on the previous attempt; rebuild
                    # EdgeHub's cloud proxy by reconnecting before resending.
                    logger("patch {} not received, reconnecting to rebuild EdgeHub cloud proxy".format(i))
                    await client.disconnect2()
                    await connect2_with_retry(client)
                    await client.enable_twin()

                logger("sending patch {} (attempt {})".format(i, attempt + 1))
                await patch_desired_props(registry, client, twin_sent)
                logger("patch {} sent".format(i))

                try:
                    await asyncio.wait_for(
                        asyncio.shield(patch_future), timeout=wait_interval
                    )
                    logger("patch {} received".format(i))
                    break
                except asyncio.TimeoutError:
                    if patch_future.done():
                        patch_future.result()  # propagate if it failed
                        logger("patch {} received (late)".format(i))
                        break
                    if attempt < len(wait_schedule) - 1:
                        logger("patch {} not received after {}s".format(i, wait_interval))
                    else:
                        patch_future.cancel()
                        try:
                            await patch_future
                        except (asyncio.CancelledError, Exception):
                            pass
                        assert False, "Timed out waiting for desired property patch {} after {} send attempts".format(i, len(wait_schedule))

    @pytest.mark.it(
        "Can set reported properties which can be successfully retrieved by the service"
    )
    async def test_twin_reported_props(self, client, registry):
        if limitations.needs_manual_connect(client):
            await connect2_with_retry(client)

        properties_sent = sample_content.make_reported_props()

        await client.enable_twin()
        await twin_op_with_retry(
            lambda p=properties_sent: client.patch_twin(p), "patch_twin"
        )

        await wait_for_reported_properties_update(
            properties_sent=properties_sent, client=client, registry=registry
        )

    @pytest.mark.it(
        "Can set reported properties 5 times and retrieve them from the service"
    )
    async def test_twin_reported_props_5_times(self, client, registry):
        if limitations.needs_manual_connect(client):
            await connect2_with_retry(client)

        await client.enable_twin()

        for iteration in range(0, 5):
            properties_sent = sample_content.make_reported_props()

            # Sending the same reported properties again is idempotent, so this is safe to retry.
            # The value is bound as a default argument so the retry cannot pick up a later value.
            await twin_op_with_retry(
                lambda p=properties_sent: client.patch_twin(p),
                "patch_twin {}/5".format(iteration + 1),
            )

            await wait_for_reported_properties_update(
                properties_sent=properties_sent, client=client, registry=registry
            )
