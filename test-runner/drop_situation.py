# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import asyncio
from adapters import adapter_config
from horton_settings import settings


class DropSituationBaseClass(object):
    @pytest.fixture(scope="class", autouse=True)
    def extend_rest_timeout(self, request, logger):
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

    @pytest.fixture(autouse=True)
    def reconnect_after_each_test(self, request, logger, test_module_wrapper_api):
        # if this test is going to drop packets, add a finalizer to make sure we always stop
        # stop dropping it when we're done.  Calling network_connect_sync twice in a row is allowed.
        def finalizer():
            logger("in finalizer: no longer dropping packets")
            test_module_wrapper_api.network_reconnect_sync()

        request.addfinalizer(finalizer)

    async def start_dropping(
        self, *, test_module_wrapper_api, logger, drop_mechanism, test_module_transport
    ):
        logger("start drop packets")
        await test_module_wrapper_api.network_disconnect(
            test_module_transport, drop_mechanism
        )

    async def wait_for_disconnection_event(self, *, client, logger):
        status = await client.get_connection_status()
        assert status == "connected"

        logger("waiting for client disconnection event")
        status = await client.wait_for_connection_status_change()
        assert status == "disconnected"
        logger("client disconnection event received")

    async def stop_dropping(self, *, test_module_wrapper_api, logger):
        logger("stop dropping packets")
        await test_module_wrapper_api.network_reconnect()

    async def wait_for_reconnection_event(self, *, client, logger):
        logger("waiting for client reconnection event")
        status = await client.wait_for_connection_status_change()
        assert status == "connected"
        logger("client reconnection event received")


class NetworkDroppedAndClientStillConnected(DropSituationBaseClass):
    """
    Tests using this class will disconnect the network before making
    the API call that we're testing.  This way, the SDK thinks it's still
    connected, but it's not.  The initial network call should fail, and the
    SDK retry logic should catch this and retry the operation until it succeeds.
    """

    @pytest.fixture
    def before_api_call(
        self, drop_mechanism, test_module_wrapper_api, logger, test_module_transport
    ):
        async def func():
            await self.start_dropping(
                test_module_wrapper_api=test_module_wrapper_api,
                logger=logger,
                drop_mechanism=drop_mechanism,
                test_module_transport=test_module_transport,
            )

        return func

    @pytest.fixture
    def after_api_call(self, client, test_module_wrapper_api, logger):
        async def func():
            await self.wait_for_disconnection_event(client=client, logger=logger)
            await asyncio.sleep(5)
            await self.stop_dropping(
                test_module_wrapper_api=test_module_wrapper_api, logger=logger
            )
            await self.wait_for_reconnection_event(client=client, logger=logger)
            await asyncio.sleep(5)

        return func


class NetworkDroppedAndClientDisconnected(DropSituationBaseClass):
    """
    Tests using this class will disconnect the network and wait for the
    SDK to notice the disconnection before making the API call that we're
    testing.  This way, the SDK knows that it's not connected.  The SDK
    should try to reconnect the client and fail.  Retry logic should catch
    this and retry the operation until it succeeds.
    """

    @pytest.fixture
    def before_api_call(
        self,
        client,
        drop_mechanism,
        test_module_wrapper_api,
        logger,
        test_module_transport,
    ):
        async def func():
            await self.start_dropping(
                test_module_wrapper_api=test_module_wrapper_api,
                logger=logger,
                drop_mechanism=drop_mechanism,
                test_module_transport=test_module_transport,
            )
            await self.wait_for_disconnection_event(client=client, logger=logger)

        return func

    @pytest.fixture
    def after_api_call(self, client, test_module_wrapper_api, logger):
        async def func():
            await asyncio.sleep(5)
            await self.stop_dropping(
                test_module_wrapper_api=test_module_wrapper_api, logger=logger
            )
            await self.wait_for_reconnection_event(client=client, logger=logger)
            await asyncio.sleep(5)

        return func


class ClientDisconnectedAndNetworkAvailable(DropSituationBaseClass):
    """
    Tests using this class will start with the client disconnected
    but the network available.
    """

    @pytest.fixture
    def before_api_call(
        self,
        client,
        drop_mechanism,
        test_module_wrapper_api,
        logger,
        test_module_transport,
    ):
        async def func():
            await client.disconnect2()

        return func

    @pytest.fixture
    def after_api_call(self, client, test_module_wrapper_api, logger):
        async def func():
            pass

        return func


class ClientDisconnectedAndNetworkNotAvailable(DropSituationBaseClass):
    @pytest.fixture
    def before_api_call(
        self,
        client,
        drop_mechanism,
        test_module_wrapper_api,
        logger,
        test_module_transport,
    ):
        async def func():
            await client.disconnect2()
            await self.start_dropping(
                test_module_wrapper_api=test_module_wrapper_api,
                logger=logger,
                drop_mechanism=drop_mechanism,
                test_module_transport=test_module_transport,
            )

        return func

    @pytest.fixture
    def after_api_call(self, client, test_module_wrapper_api, logger):
        async def wait_and_reconnect():
            await asyncio.sleep(30)
            await self.stop_dropping(
                test_module_wrapper_api=test_module_wrapper_api, logger=logger
            )

        async def func():
            asyncio.ensure_future(wait_and_reconnect())

        return func

    pass
