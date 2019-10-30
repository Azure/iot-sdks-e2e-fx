# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


import pytest
import pathlib
import adapters
import logging
import traceback
from adapters import adapter_config, print_message
from identity_helpers import ensure_edge_environment_variables
import runtime_config_templates
import runtime_config
import runtime_capabilities
import scenarios
from distutils.version import LooseVersion
from fixtures import (
    test_string,
    test_string_2,
    test_object_stringified,
    test_object_stringified_2,
    logger,
    eventhub,
    registry,
    friend,
    leaf_device,
    service,
    test_device,
    test_module,
    test_module_wrapper_api,
    test_payload,
    sample_reported_props,
    sample_desired_props,
    sample_payload,
)
from log_fixtures import (
    pytest_runtest_makereport,
    session_log_fixture,
    module_log_fixture,
    function_log_fixture,
)

# default to logging.INFO
logging.basicConfig(level=logging.INFO)
# AMQP is chatty at INFO level.  Dial this down to WARNING.
logging.getLogger("uamqp").setLevel(level=logging.WARNING)
logging.getLogger("paho").setLevel(level=logging.DEBUG)
logging.getLogger("adapters.direct_azure_rest.amqp_service_client").setLevel(
    level=logging.WARNING
)  # info level can leak credentials into the log
logging.getLogger("azure.iot.device").setLevel(level=logging.INFO)


ensure_edge_environment_variables()


def pytest_addoption(parser):
    parser.addoption(
        "--scenario",
        help="scenario to run",
        required=True,
        type=str,
        choices=scenarios.scenarios.keys(),
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
        "--pythonv1-wrapper",
        action="store_true",
        default=False,
        help="run tests for pythonv1 wrapper",
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
        help="run tests against local module (probably in debugger)",
    )
    parser.addoption(
        "--transport",
        action="store",
        default="mqtt",
        help="transport to use for test",
        choices=runtime_config_templates.valid_transports,
    )
    parser.addoption(
        "--pythonv2-wrapper",
        action="store_true",
        default=False,
        help="run tests for the pythonv2 wrapper",
    )
    parser.addoption(
        "--ppdirect-wrapper",
        action="store_true",
        default=False,
        help="run tests for the pythonv2 wrapper in-proc",
    )
    parser.addoption(
        "--debug-container",
        action="store_true",
        default=False,
        help="adjust run for container debugging (disable timeouts)",
    )
    parser.addoption(
        "--async",
        action="store_true",
        default=False,
        help="run async tests (currently pythonv2 only)",
    )


# langauge that we're running against
language = ""

# Transport to use for test
transport = "mqtt"


skip_for_c_amqp = set(["receivesInputMessages", "callsSendOutputEvent"])

skip_for_c_mqttws = set(["receivesInputMessages"])

skip_for_c_connection_string = set(
    ["invokesModuleMethodCalls", "invokesDeviceMethodCalls"]
)


def _get_marker(item, marker):
    if LooseVersion(pytest.__version__) < LooseVersion("3.6"):
        return item.get_marker(marker)
    else:
        return item.get_closest_marker(marker)


def remove_tests_not_in_marker_list(items, markers):
    """
    remove all items that don't have one of the specified markers set
    """
    remaining = []
    for item in items:
        keep = False
        for marker in markers:
            if _get_marker(item, marker):
                keep = True
        if keep:
            remaining.append(item)

    items[:] = remaining


def skip_tests_by_marker(items, skiplist, reason):
    skip_me = pytest.mark.skip(reason=reason)
    for markname in skiplist:
        print("skipping {} because {}:".format(markname, reason))
        for item in items:
            if markname in item.keywords:
                item.add_marker(skip_me)
                print("  " + str(item))


__tracebackhide__ = True


def pytest_collection_modifyitems(config, items):
    print("")

    test_module_use_connection_string = False
    local = False

    scenario = scenarios.scenarios[config.getoption("--scenario")]
    remove_tests_not_in_marker_list(items, scenario.pytest_markers)

    transport = config.getoption("--transport")
    print("Using " + transport)

    if config.getoption("--local"):
        print("Running against local module")
        local = True
        test_module_use_connection_string = True

    if (
        test_module_use_connection_string
        or scenarios.CONNECT_WITH_ENVIRONMENT not in scenario.scenario_flags
    ):
        print("Using connection string to connect")
        test_module_use_connection_string = True

    if config.getoption("--node-wrapper"):
        print("Using node wrapper")
        language = "node"
    elif config.getoption("--csharp-wrapper"):
        print("Using csharp wrapper")
        language = "csharp"
    elif config.getoption("--pythonv1-wrapper"):
        print("Using pythonv1 wrapper")
        language = "pythonv1"
    elif config.getoption("--c-wrapper"):
        print("Using C wrapper")
        language = "c"
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
    elif config.getoption("--pythonv2-wrapper"):
        print("Using pythonv2 wrapper")
        language = "pythonv2"
    elif config.getoption("--ppdirect-wrapper"):
        print("Using pythonv2 wrapper in-proc")
        language = "ppdirect"
    else:
        print("you must specify a wrapper")
        raise Exception("no wrapper specified")

    runtime_config.set_runtime_configuration(scenario, language, transport, local)
    skip_list = runtime_capabilities.get_skip_list(language)
    for cap in runtime_capabilities.get_all_capabilities_flags():
        if not runtime_capabilities.get_test_module_capabilities_flag(cap):
            skip_list.append(cap)

    # make sure the network is connected before starting (this can happen with interrupted runs)
    if runtime_capabilities.get_test_module_capabilities_flag("v2_connect_group"):
        runtime_config.get_test_module_wrapper_api().network_reconnect_sync()

    skip_tests_by_marker(
        items, skip_list, "it isn't implemented in the {} wrapper".format(language)
    )

    if config.getoption("--async"):
        test_module_supports_async = runtime_capabilities.get_test_module_capabilities_flag(
            "supports_async"
        )
        if test_module_supports_async:
            runtime_capabilities.set_test_module_flag("test_async", True)
        else:
            raise Exception("--async specified, but test module does not support async")

    if getattr(config, "_origargs", None):
        adapters.print_message("HORTON: starting run: {}".format(config._origargs))
    elif getattr(config, "invocation_params", None):
        adapters.print_message(
            "HORTON: starting run: {}".format(config.invocation_params.args)
        )

    if config.getoption("--debug-container"):
        print("Debugging the container.  Removing all timeouts")
        adapter_config.default_api_timeout = 3600
        config._env_timeout = 0
