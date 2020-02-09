# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import adapters
import pytest
import traceback
from horton_settings import settings
from horton_logging import logger

# from https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "teardown":
        if rep.failed:
            logger("teardown:   " + str(rep.outcome))
    else:
        # set a report attribute for each phase of a call, which can
        # be 'setup', 'call', 'teardown'
        setattr(item, "rep_" + rep.when, rep)


dashes = "".join(("-" for _ in range(0, 30)))
separator = "{} CLEANUP {} {}".format(dashes, "{}", dashes)

# BKTODO: move this out of this file into it's own file
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    yield

    # BKTODO: this should iterate over settings
    if getattr(settings, "eventhub", None) and settings.eventhub.client:
        logger(separator.format("eventhub"))
        settings.eventhub.client.disconnect_sync()

    if getattr(settings, "registry", None) and settings.registry.client:
        logger(separator.format("registry"))
        settings.registry.client.disconnect_sync()

    if getattr(settings, "friend", None) and settings.friend.client:
        logger(separator.format("friend module"))
        settings.friend.client.disconnect_sync()

    if getattr(settings, "test_module", None) and settings.test_module.client:
        logger(separator.format("test module"))
        settings.test_module.client.disconnect_sync()

    if getattr(settings, "leaf_device", None) and settings.leaf_device.client:
        logger(separator.format("leaf device"))
        settings.leaf_device.client.disconnect_sync()

    if getattr(settings, "test_device", None) and settings.test_device.client:
        logger(separator.format("device"))
        settings.test_device.client.disconnect_sync()

    if getattr(settings, "service", None) and settings.service.client:
        logger(separator.format("service"))
        settings.service.client.disconnect_sync()

    if settings.test_module.capabilities.checks_for_leaks:
        settings.test_module.wrapper_api.send_command_sync("check_for_leaks")


separator = "".join("-" for _ in range(0, 132))


@pytest.fixture(scope="function", autouse=True)
def function_log_fixture(request):
    logger(separator)
    logger(
        "HORTON: Entering function '{}.{}' '{}'".format(
            request.module.__name__, request.cls.__name__, request.node.name
        )
    )

    def fin():
        logger(separator)
        if hasattr(request.node, "rep_setup"):
            logger("setup:      " + str(request.node.rep_setup.outcome))
        if hasattr(request.node, "rep_call"):
            logger("call:       " + str(request.node.rep_call.outcome))
        logger(separator)
        logger(
            "HORTON: Cleaning up after function {}".format(request.function.__name__)
        )

        try:
            adapters.cleanup_test_objects()
        except Exception:
            logger("Exception in cleanup")
            logger(traceback.format_exc())
            raise
        finally:
            logger(
                "HORTON: Exiting function '{}.{}' '{}'".format(
                    request.module.__name__, request.cls.__name__, request.node.name
                )
            )

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=True)
def module_log_fixture(request):
    logger("HORTON: Entering module {}".format(request.module.__name__))

    def fin():
        logger("HORTON: Exiting module {}".format(request.module.__name__))

    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def session_log_fixture(request):
    logger("HORTON: Preforming pre-session cleanup")
    adapters.cleanup_test_objects()
    logger("HORTON: pre-session cleanup complete")

    def fin():
        logger("Preforming post-session cleanup")
        try:
            adapters.cleanup_test_objects()
        except Exception:
            logger("Exception in cleanup")
            logger(traceback.format_exc())
            raise
        finally:
            logger("HORTON: post-session cleanup complete")

    request.addfinalizer(fin)
