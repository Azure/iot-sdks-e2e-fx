# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import adapters
import pytest
import logging
import traceback
from adapters import print_message

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
    print_message(separator)
    print_message(
        "HORTON: Entering function '{}.{}' '{}'".format(
            request.module.__name__, request.cls.__name__, request.node.name
        )
    )

    def fin():
        print_message(separator)
        if hasattr(request.node, "rep_setup"):
            print_message("setup:      " + str(request.node.rep_setup.outcome))
        if hasattr(request.node, "rep_call"):
            print_message("call:       " + str(request.node.rep_call.outcome))
        if hasattr(request.node, "rep_teardown"):
            print_message("teardown:   " + str(request.node.rep_teardown.outcome))
        print_message(separator)
        print_message(
            "HORTON: Cleaning up after function {}".format(request.function.__name__)
        )

        try:
            adapters.cleanup_test_objects()
        except Exception:
            print_message("Exception in cleanup")
            print_message(traceback.format_exc())
            raise
        finally:
            print_message(
                "HORTON: Exiting function '{}.{}' '{}'".format(
                    request.module.__name__, request.cls.__name__, request.node.name
                )
            )

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=True)
def module_log_fixture(request):
    print_message("HORTON: Entering module {}".format(request.module.__name__))

    def fin():
        print_message("HORTON: Exiting module {}".format(request.module.__name__))

    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def session_log_fixture(request):
    print_message("HORTON: Preforming pre-session cleanup")
    adapters.cleanup_test_objects()
    print_message("HORTON: pre-session cleanup complete")

    def fin():
        print_message("Preforming post-session cleanup")
        try:
            adapters.cleanup_test_objects()
        except Exception:
            print_message("Exception in cleanup")
            print_message(traceback.format_exc())
            raise
        finally:
            print_message("HORTON: post-session cleanup complete")

    request.addfinalizer(fin)
