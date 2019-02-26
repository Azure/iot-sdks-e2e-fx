#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


import pytest
import signal
import environment
import adapters
from adapters import print_message as log_message
from docker_log_watcher import DockerLogWatcher
from identity_helpers import ensure_edge_environment_variables

ensure_edge_environment_variables()


def pytest_addoption(parser):
    parser.addoption(
        "--direct-to-iothub",
        action="store_true",
        default=False,
        help="go directly to iothub for tests (no edgehub)",
    )
    parser.addoption(
        "--node-wrapper",
        action="store_true",
        default=False,
        help="run tests for node wrapper",
    )
    parser.addoption(
        "--csharp-wrapper",
        action="store_true",
        default=False,
        help="run tests for csharp wrapper",
    )
    parser.addoption(
        "--python-wrapper",
        action="store_true",
        default=False,
        help="run tests for python wrapper",
    )
    parser.addoption(
        "--c-wrapper",
        action="store_true",
        default=False,
        help="run tests for c wrapper",
    )
    parser.addoption(
        "--java-wrapper",
        action="store_true",
        default=False,
        help="run tests for java wrapper",
    )
    parser.addoption(
        "--local",
        action="store_true",
        default=False,
        help="run tests against local module (probably in debugger",
    )
    parser.addoption(
        "--force-connection-string",
        action="store_true",
        default=False,
        help="force use of connection string for modules",
    )
    parser.addoption(
        "--transport",
        action="store",
        default="mqtt",
        help="transport: mqtt, mqttws, amqp, amqpws, or http",
    )
    parser.addoption(
        "--pythonpreview-wrapper",
        action="store_true",
        default=False,
        help="run tests for the python preview wrapper",
    )
    parser.addoption(
        "--ppdirect-wrapper",
        action="store_true",
        default=False,
        help="run tests for the python preview wrapper in-proc",
    )


# langauge that we're running against
language = ""

# True if we're debugging against a local module rather than a container
local = False

# True if we're bypassing edgeHub
direct_to_iothub = False

# True to connect the module using a connection string
test_module_use_connection_string = False

# Transport to use for test
transport = "mqtt"

# Valid transports
valid_transports = ["mqtt", "mqttws", "amqp", "amqpws"]

skip_for_node = set([])

skip_for_csharp = set(
    ["module_under_test_has_device_wrapper", "handlesLoopbackMessages"]
)


skip_for_python = set(
    [
        "module_under_test_has_device_wrapper",
        "invokesModuleMethodCalls",
        "invokesDeviceMethodCalls",
    ]
)

skip_for_pythonpreview = set(
    [
        "receivesInputMessages",
        "receivesMethodCalls",
        "invokesModuleMethodCalls",
        "invokesDeviceMethodCalls",
        "supportsTwin",
        "handlesLoopbackMessages",
        "module_under_test_has_device_wrapper",
    ]
)

skip_for_c = set(["module_under_test_has_device_wrapper"])

skip_for_c_amqp = set(["receivesInputMessages", "callsSendOutputEvent"])

skip_for_c_mqttws = set(["receivesInputMessages"])

skip_for_c_connection_string = set(
    ["invokesModuleMethodCalls", "invokesDeviceMethodCalls"]
)

skip_for_java = set(["module_under_test_has_device_wrapper", "supportsTwin"])


def skip_tests_by_marker(items, skiplist, reason):
    skip_me = pytest.mark.skip(reason=reason)
    for markname in skiplist:
        print("skipping {} because {}:".format(markname, reason))
        for item in items:
            if markname in item.keywords:
                item.add_marker(skip_me)
                print("  " + str(item))


__tracebackhide__ = True


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
        log_message(
            "HORTON: Cleaning up after function {}".format(request.function.__name__)
        )
        adapters.cleanup_test_objects()
        log_message("HORTON: Exiting function {}".format(request.function.__name__))
        log_watcher.flush_and_disable()

    request.addfinalizer(fin)


@pytest.fixture(scope="module", autouse=True)
def module_log_fixture(request):
    print("")
    log_message("HORTON: Entering module {}".format(request.module.__name__))

    def fin():
        print("")
        log_message("HORTON: Exiting module {}".format(request.module.__name__))

    request.addfinalizer(fin)


@pytest.fixture(scope="session", autouse=True)
def session_log_fixture(request):
    print("")
    log_message("HORTON: Preforming pre-session cleanup")
    adapters.cleanup_test_objects()
    log_message("HORTON: pre-session cleanup complete")

    def fin():
        print("")
        log_message("Preforming post-session cleanup")
        adapters.cleanup_test_objects()
        log_message("HORTON: post-session cleanup complete")
        if log_watcher:
            log_watcher.terminate()

    request.addfinalizer(fin)


def pytest_collection_modifyitems(config, items):
    global language
    global local
    global direct_to_iothub
    global test_module_use_connection_string
    global transport

    print("")

    transport = config.getoption("--transport")
    if transport in valid_transports:
        print("Using " + transport)
    else:
        pytest.fail("Transport {} is invalid".format(transport))

    if config.getoption("--local"):
        print("Running against local module")
        local = True
        test_module_use_connection_string = True

    if test_module_use_connection_string or config.getoption(
        "--force-connection-string"
    ):
        print("Using connection string to connect")
        test_module_use_connection_string = True

    if config.getoption("--direct-to-iothub"):
        print("Going directly to iothub")
        direct_to_iothub = True

    if config.getoption("--node-wrapper"):
        print("Using node wrapper")
        language = "node"
        skip_tests_by_marker(
            items, skip_for_node, "it isn't implemented in the node wrapper"
        )
    elif config.getoption("--csharp-wrapper"):
        print("Using csharp wrapper")
        language = "csharp"
        skip_tests_by_marker(
            items, skip_for_csharp, "it isn't implemented in the csharp wrapper"
        )
    elif config.getoption("--python-wrapper"):
        print("Using python wrapper")
        language = "python"
        skip_tests_by_marker(
            items, skip_for_python, "it isn't implemented in the python wrapper"
        )
    elif config.getoption("--c-wrapper"):
        print("Using C wrapper")
        language = "c"
        skip_tests_by_marker(items, skip_for_c, "it isn't implemented in the c wrapper")
        if test_module_use_connection_string:
            skip_tests_by_marker(
                items,
                skip_for_c_connection_string,
                "it isn't implemented in the c wrapper with connection strings",
            )
        if transport.startswith("amqp"):
            skip_tests_by_marker(
                items,
                skip_for_c_amqp,
                "it isn't implemented in the c wrapper with amqp",
            )
        if transport.startswith("mqttws"):
            skip_tests_by_marker(
                items,
                skip_for_c_mqttws,
                "it isn't implemented in the c wrapper with mqtt-ws",
            )
    elif config.getoption("--java-wrapper"):
        print("Using Java wrapper")
        language = "java"
        skip_tests_by_marker(
            items, skip_for_java, "it isn't implemented in the java wrapper"
        )
    elif config.getoption("--pythonpreview-wrapper"):
        print("Using python-preview wrapper")
        language = "pythonpreview"
        skip_tests_by_marker(
            items,
            skip_for_pythonpreview,
            "it isn't implemented in the new python wrapper",
        )
    elif config.getoption("--ppdirect-wrapper"):
        print("Using python-preview wrapper in-proc")
        language = "ppdirect"
        skip_tests_by_marker(
            items,
            skip_for_pythonpreview,
            "it isn't implemented in the new python wrapper",
        )
    else:
        print("you must specify a wrapper")
        raise Exception("no wrapper specified")

    environment.setupExecutionEnvironment()
    adapters.print_message("HORTON: starting run: {}".format(config._origargs))
    set_up_log_watcher()


def set_up_log_watcher():
    global log_watcher
    filters = ["PYTEST: ", "Getting next batch", "Obtained next batch"]
    container_names = [
        "edgeHub",
        "friendMod",
        environment.runtime_config.test_module.module_id,
    ]
    log_watcher = DockerLogWatcher(container_names, filters)
