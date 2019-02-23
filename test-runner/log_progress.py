#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import pytest
import adapters
from adapters import print_message as log_message

def install_progress_fixtures():
    print("setting up fixtures to log execution progress")

    # this is all we need to do.  By defining the fixtures below with the 
    # pytest.fixture decrator, we are effectively attaching these fixtures
    # to all of our tests


# from https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be 'setup', 'call', 'teardown'

    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="function", autouse=True)
def function_log_fixture(request):
    global log_watcher
    log_watcher.enable()
    print("")
    log_message("HORTON: Entering function {}".format(request.function.__name__))

    def fin():
        print("")
        if hasattr(request.node, "rep_setup"):
            log_message("setup:      " + str(request.node.rep_setup.outcome))
        if hasattr(request.node, "rep_call"):
            log_message("call:       " + str(request.node.rep_call.outcome))
        if hasattr(request.node, "rep_teardown"):
            log_message("teardown:   " + str(request.node.rep_call.outcome))
        log_messsage("HORTON: Cleaning up after function {}".format(request.function.__name__))
        adapters.cleanup_test_objects()
        log_messsage("HORTON: Exiting function {}".format(request.function.__name__))
        log_watcher.flush_and_disable()

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=True)
def module_log_fixture(request):
    print("")
    log_messsage("HORTON: Entering module {}".format(request.module.__name__))

    def fin():
        print("")
        log_messsage("HORTON: Exiting module {}".format(request.module.__name__))

    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def session_log_fixture(request):
    print("")
    log_messsage("HORTON: Preforming pre-session cleanup")
    adapters.cleanup_test_objects()
    log_messsage("HORTON: pre-session cleanup complete")

    def fin():
        print("")
        log_messsage("Preforming post-session cleanup")
        adapters.cleanup_test_objects()
        log_messsage("HORTON: post-session cleanup complete")
        if log_watcher:
            log_watcher.terminate()

    request.addfinalizer(fin)


def set_up_log_watcher():
    global log_watcher
    filters = ["PYTEST: ", "Getting next batch", "Obtained next batch"]
    container_names = ["edgeHub", "friendMod", environment.module_id]
    log_watcher = DockerLogWatcher(container_names, filters)
