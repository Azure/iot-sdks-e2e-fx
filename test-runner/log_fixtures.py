# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import adapters
import pytest
import logging
import traceback
from adapters import adapter_config

# from https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be 'setup', 'call', 'teardown'

    setattr(item, "rep_" + rep.when, rep)


separator = "".join("-" for _ in range(0, 132))


@pytest.fixture(scope="function", autouse=True)
def function_log_fixture(request):
    adapter_config.logger(separator)
    adapter_config.logger(
        "HORTON: Entering function '{}.{}' '{}'".format(
            request.module.__name__, request.cls.__name__, request.node.name
        )
    )

    def fin():
        adapter_config.logger(separator)
        if hasattr(request.node, "rep_setup"):
            adapter_config.logger("setup:      " + str(request.node.rep_setup.outcome))
        if hasattr(request.node, "rep_call"):
            adapter_config.logger("call:       " + str(request.node.rep_call.outcome))
        if hasattr(request.node, "rep_teardown"):
            adapter_config.logger(
                "teardown:   " + str(request.node.rep_teardown.outcome)
            )
        adapter_config.logger(separator)
        adapter_config.logger(
            "HORTON: Cleaning up after function {}".format(request.function.__name__)
        )

        try:
            adapters.cleanup_test_objects()
        except Exception:
            adapter_config.logger("Exception in cleanup")
            adapter_config.logger(traceback.format_exc())
            raise
        finally:
            adapter_config.logger(
                "HORTON: Exiting function '{}.{}' '{}'".format(
                    request.module.__name__, request.cls.__name__, request.node.name
                )
            )

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=True)
def module_log_fixture(request):
    adapter_config.logger("HORTON: Entering module {}".format(request.module.__name__))

    def fin():
        adapter_config.logger(
            "HORTON: Exiting module {}".format(request.module.__name__)
        )

    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def session_log_fixture(request):
    adapter_config.logger("HORTON: Preforming pre-session cleanup")
    adapters.cleanup_test_objects()
    adapter_config.logger("HORTON: pre-session cleanup complete")

    def fin():
        adapter_config.logger("Preforming post-session cleanup")
        try:
            adapters.cleanup_test_objects()
        except Exception:
            adapter_config.logger("Exception in cleanup")
            adapter_config.logger(traceback.format_exc())
            raise
        finally:
            adapter_config.logger("HORTON: post-session cleanup complete")

    request.addfinalizer(fin)
