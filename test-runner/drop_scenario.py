# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
import pytest_asyncio
from adapters import adapter_config
from horton_settings import settings
from horton_logging import logger

try:
    async_fixture = pytest_asyncio.fixture
except AttributeError:
    async_fixture = pytest.fixture


class DropScenarioBaseClass(object):
    @pytest.fixture(scope="class", autouse=True)
    def extend_rest_timeout(self, request):
        previous_timeout = adapter_config.default_api_timeout
        adapter_config.default_api_timeout = max(300, previous_timeout)
        logger(
            "Starting test class: Adjusting REST timeout to {} seconds".format(
                adapter_config.default_api_timeout
            )
        )

        def fin():
            adapter_config.default_api_timeout = previous_timeout
            logger(
                "Finishing test class: Replacing old REST timeout of {} seconds".format(
                    previous_timeout
                )
            )

        request.addfinalizer(fin)

    @pytest.fixture(
        params=[
            pytest.param("DROP", id="Drop using iptables DROP"),
            pytest.param("REJECT", id="Drop using iptables REJECT"),
        ]
    )
    def drop_mechanism(self, request):
        """
        Parametrized fixture which lets our tests run against the full set
        of dropping mechanisms.  Every test in this file will run using each value
        for this array of parameters.
        """
        return request.param

    @pytest.fixture
    def test_module_transport(self):
        return settings.test_module.transport

    @async_fixture(autouse=True)
    async def reconnect_after_each_test(self, system_control):
        # if this test is going to drop packets, add a finalizer to make sure we always stop
        # stop dropping it when we're done.  Calling reconnect twice in a row is allowed.
        try:
            yield
        finally:
            logger("in finalizer: no longer dropping packets")
            await system_control.reconnect_network()

    async def start_dropping(
        self, *, system_control, drop_mechanism, test_module_transport
    ):
        logger("start drop packets")
        await system_control.disconnect_network(drop_mechanism)

    async def wait_for_disconnection_event(self, *, client):
        status = await client.get_connection_status()
        assert status == "connected"

        logger("waiting for client disconnection event")
        await client.wait_for_connection_status_change("disconnected")
        logger("client disconnection event received")

    async def stop_dropping(self, *, system_control):
        logger("stop dropping packets")
        await system_control.reconnect_network()

    async def wait_for_reconnection_event(self, *, client):
        logger("waiting for client reconnection event")
        await client.wait_for_connection_status_change("connected")
        logger("client reconnection event received")


class NetworkGlitchClientConnected(DropScenarioBaseClass):
    """
    Tests using this class will disconnect the network before making
    the API call that we're testing.  This way, the SDK thinks it's still
    connected, but it's not.  The initial network call should fail, and the
    SDK retry logic should catch this and retry the operation until it succeeds.
    """

    @pytest.fixture
    def before_api_call(
        self, client, drop_mechanism, system_control, test_module_transport
    ):
        async def func():
            await client.connect2()
            assert await client.get_connection_status() == "connected"

            await self.start_dropping(
                system_control=system_control,
                drop_mechanism=drop_mechanism,
                test_module_transport=test_module_transport,
            )

        return func

    @pytest.fixture
    def after_api_call(self, client, system_control):
        async def func():
            await self.wait_for_disconnection_event(client=client)
            await asyncio.sleep(5)
            await self.stop_dropping(system_control=system_control)
            await self.wait_for_reconnection_event(client=client)
            await asyncio.sleep(5)

        return func


class NetworkGlitchClientDisconnected(DropScenarioBaseClass):
    """
    Tests using this class will disconnect the network and wait for the
    SDK to notice the disconnection before making the API call that we're
    testing.  This way, the SDK knows that it's not connected.  The SDK
    should try to reconnect the client and fail.  Retry logic should catch
    this and retry the operation until it succeeds.
    """

    @pytest.fixture(
        params=[
            pytest.param("DROP", id="Drop using iptables DROP"),
            # REJECT tests no longer work here after state machine changes
            # pytest.param("REJECT", id="Drop using iptables REJECT"),
        ]
    )
    def drop_mechanism(self, request):
        """
        Parametrized fixture which lets our tests run against the full set
        of dropping mechanisms.  Every test in this file will run using each value
        for this array of parameters.
        """
        return request.param

    @pytest.fixture
    def before_api_call(
        self, client, drop_mechanism, system_control, test_module_transport
    ):
        async def func():
            await client.connect2()
            assert await client.get_connection_status() == "connected"

            await self.start_dropping(
                system_control=system_control,
                drop_mechanism=drop_mechanism,
                test_module_transport=test_module_transport,
            )
            await self.wait_for_disconnection_event(client=client)

        return func

    @pytest.fixture
    def after_api_call(self, client, system_control):
        async def func():
            await asyncio.sleep(5)
            await self.stop_dropping(system_control=system_control)
            await self.wait_for_reconnection_event(client=client)
            await asyncio.sleep(5)

        return func
