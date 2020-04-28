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
general_separator = "".join("-" for _ in range(0, 132))

# BKTODO: move this out of this file into it's own file
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_pyfunc_call(pyfuncitem):

    cleanup_separator = "{} CLEANUP {} {}".format(dashes, "{}", dashes)

    # this hook wraps test runs.  this yield runs the actual test
    outcome = yield

    try:
        # this will raise if the outcome was an exception
        outcome.get_result()

        logger(general_separator)
        logger("TEST PASSED (before cleanup)")

    except Exception as e:
        logger(general_separator)
        logger("TEST FAILED BACAUSE OF {}".format(e))

    finally:
        # BKTODO: this should iterate over settings
        if getattr(settings, "eventhub", None) and settings.eventhub.client:
            logger(cleanup_separator.format("eventhub"))
            settings.eventhub.client.disconnect_sync()
            settings.eventhub.client = None

        if getattr(settings, "registry", None) and settings.registry.client:
            logger(cleanup_separator.format("registry"))
            settings.registry.client.disconnect_sync()
            settings.registry.client = None

        if getattr(settings, "friend_module", None) and settings.friend_module.client:
            logger(cleanup_separator.format("friend module"))
            settings.friend_module.client.disconnect_sync()
            settings.friend_module.client = None

        if getattr(settings, "test_module", None) and settings.test_module.client:
            logger(cleanup_separator.format("test module"))
            settings.test_module.client.disconnect_sync()
            settings.test_module.client = None

        if getattr(settings, "leaf_device", None) and settings.leaf_device.client:
            logger(cleanup_separator.format("leaf device"))
            settings.leaf_device.client.disconnect_sync()
            settings.leaf_device.client = None

        if getattr(settings, "test_device", None) and settings.test_device.client:
            logger(cleanup_separator.format("device"))
            settings.test_device.client.disconnect_sync()
            settings.test_device.client = None

        if getattr(settings, "service", None) and settings.service.client:
            logger(cleanup_separator.format("service"))
            settings.service.client.disconnect_sync()
            settings.service.client = None

        if settings.test_module.capabilities.checks_for_leaks:
            settings.test_module.wrapper_api.send_command_sync("check_for_leaks")


@pytest.fixture(scope="function", autouse=True)
def function_log_fixture(request):
    logger(general_separator)
    logger(
        "HORTON: Entering function '{}.{}' '{}'".format(
            request.module.__name__, request.cls.__name__, request.node.name
        )
    )

    def fin():
        logger(general_separator)
        if hasattr(request.node, "rep_setup"):
            logger("setup:      " + str(request.node.rep_setup.outcome))
        if hasattr(request.node, "rep_call"):
            logger("call:       " + str(request.node.rep_call.outcome))
        logger(general_separator)
        logger(
            "HORTON: Cleaning up after function {}".format(request.function.__name__)
        )

        try:
            adapters.cleanup_test_objects_sync()
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
    adapters.cleanup_test_objects_sync()
    logger("HORTON: pre-session cleanup complete")

    def fin():
        logger("Preforming post-session cleanup")
        try:
            adapters.cleanup_test_objects_sync()
        except Exception:
            logger("Exception in cleanup")
            logger(traceback.format_exc())
            raise
        finally:
            logger("HORTON: post-session cleanup complete")

    request.addfinalizer(fin)
