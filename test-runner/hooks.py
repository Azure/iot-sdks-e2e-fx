# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import pytest
import traceback
import connections
from horton_settings import settings
from horton_logging import logger
from pytest_asyncio.plugin import wrap_in_sync


def separator(message=""):
    return message.center(132, "-")


def nodeid_to_xunit_class_and_test(nodeid):
    # nodeid: 'test_iothub_module.py::TestIotHubModuleClient::test_regression_connect_fails_with_corrupt_connection_string[SharedAccessKey-aGlsbGJpbGx5IHN1bnJpc2UK]'
    # <--becomes-->
    # xunit_class= 'test_iothub_module.TestIotHubModuleClient'
    # xunit_test 'test_regression_connect_fails_with_corrupt_connection_string[SharedAccessKey-aGlsbGJpbGx5IHN1bnJpc2UK]'

    parts = nodeid.split("::")
    xunit_class = parts[0][:-3] + "." + parts[1]
    xunit_test = parts[2]

    return (xunit_class, xunit_test)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logstart(nodeid, location):
    (xunit_class, xunit_test) = nodeid_to_xunit_class_and_test(nodeid)
    logger(separator())
    logger("HORTON: Entering function '{}' '{}'".format(xunit_class, xunit_test))


@pytest.hookimpl(trylast=True)
def pytest_runtest_logfinish(nodeid, location):
    (xunit_class, xunit_test) = nodeid_to_xunit_class_and_test(nodeid)
    logger("HORTON: Exiting function '{}' '{}'".format(xunit_class, xunit_test))


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    if settings.test_module.capabilities.checks_for_leaks:
        logger(separator("checking for leaks"))
        settings.test_module.wrapper_api.send_command_sync("check_for_leaks")
        logger(separator("done checking for leaks"))


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):

    # this hook wraps test runs.  this yield runs the actual test
    outcome = yield

    try:
        # this will raise if the outcome was an exception
        outcome.get_result()

        logger(separator("TEST PASSED (before cleanup)"))

    except Exception as e:
        logger(separator("TEST FAILED BACAUSE OF {}".format(e)))
        logger(traceback.format_exc())


async def configure_net_control():
    if settings.test_module.capabilities.net_control_app:
        try:
            settings.net_control.api = await connections.get_net_control_api()
        except Exception:
            print(
                "network control server is unavailable.  Either start the server or set net_control.adapter_address to '' in _horton_settings.json"
            )
            settings.test_module.capabilities.net_control = False

    if settings.net_control.api:
        await settings.net_control.api.reconnect()


async def session_init():
    print(separator("SESSION INIT"))
    await configure_net_control()


async def session_teardown():
    print(separator("SESSION TEARDOWN"))
    logger("Preforming post-session cleanup")
    try:
        pass
        # BKTODO
    except Exception:
        logger("Exception in cleanup")
        logger(traceback.format_exc())
        raise
    finally:
        logger("HORTON: post-session cleanup complete")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtestloop(session):

    loop = asyncio.get_event_loop_policy().new_event_loop()
    wrap_in_sync(session_init, loop)()
    try:
        yield
    finally:
        wrap_in_sync(session_teardown, loop)()
        loop.close()
