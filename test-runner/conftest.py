# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.


import pytest
import pathlib
import adapters
import logging
import traceback
from adapters import adapter_config
from dump_object import dump_object
import runtime_capabilities
import scenarios
from distutils.version import LooseVersion
from horton_settings import settings
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


def pytest_addoption(parser):
    parser.addoption(
        "--scenario",
        help="scenario to run",
        required=True,
        type=str,
        choices=scenarios.scenarios.keys(),
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
        choices=["mqtt", "mqttws", "amqp", "amqpws"],
    )
    parser.addoption(
        "--direct-python",
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


def set_transport(transport):
    print("Using " + transport)
    settings.friend_module.transport = "mqtt"
    settings.test_module.transport = transport
    settings.leaf_device.transport = transport
    settings.test_device.transport = transport


def set_local():
    print("Running against local module")
    if settings.test_module.connection_type == "environment":
        settings.test_module.connection_type = "connection_string_with_edge_gateway"
        # any objects that were previously using the test module host port now use
        # the test module container port.
        for obj in (settings.test_module, settings.test_device, settings.leaf_device):
            if obj.host_port == settings.test_module.host_port:
                obj.adapter_address = "http://localhost:{}".format(
                    settings.test_module.container_port
                )


def set_python_direct():
    print("Using pythonv2 wrapper in-proc")
    settings.test_module.adapter_address = "direct_python"
    settings.test_device.adapter_address = "direct_python"
    settings.leaf_device.adapter_address = "direct_python"


def set_async():
    if (
        settings.test_module.device_id
        and settings.test_module.capabilities.supports_async
    ):
        settings.test_module.wrapper_api.set_flags_sync({"test_async": True})
    else:
        raise Exception("--async specified, but test module does not support async")


def add_service_settings():
    class ServiceSettings:
        pass

    settings.eventhub = ServiceSettings()
    settings.eventhub.name = "eventhub"
    settings.eventhub.connection_string = settings.iothub.connection_string
    settings.eventhub.adapter_address = "direct_rest"

    settings.registry = ServiceSettings()
    settings.registry.name = "registry"
    settings.registry.connection_string = settings.iothub.connection_string
    settings.registry.adapter_address = settings.test_module.adapter_address

    settings.service = ServiceSettings()
    settings.service.name = "service"
    settings.service.connection_string = settings.iothub.connection_string
    settings.service.adapter_address = settings.test_module.adapter_address


def adjust_surfaces_for_missing_implementations():
    if (
        settings.test_module.language
        not in runtime_capabilities.language_has_service_client
    ):
        settings.registry.adapter_address = "direct_rest"
        settings.service.adapter_address = "direct_rest"

    if settings.test_module.language not in (
        runtime_capabilities.language_has_leaf_device_client
        + runtime_capabilities.language_has_full_device_client
    ):
        settings.leaf_device.adapter_address = settings.friend_module.adapter_address
        settings.leaf_device.container_port = settings.friend_module.container_port
        settings.leaf_device.host_port = settings.friend_module.host_port

    if (
        settings.test_module.language
        not in runtime_capabilities.language_has_full_device_client
    ):
        settings.test_device.adapter_address = None


def only_include_scenario_tests(items, scenario_name):
    scenario = scenarios.scenarios[scenario_name]
    remove_tests_not_in_marker_list(items, scenario.pytest_markers)


def skip_unsupported_tests(items):
    if settings.test_module.language == "c":
        print("Using C wrapper")
        if settings.test_module.connection_type.startswith("connection_string"):
            skip_tests_by_marker(
                items,
                skip_for_c_connection_string,
                "it isn't implemented in the c wrapper with connection strings",
            )
        if settings.test_module.transport.startswith("amqp"):
            skip_tests_by_marker(
                items,
                skip_for_c_amqp,
                "it isn't implemented in the c wrapper with amqp",
            )
        if settings.test_module.transport.startswith("mqttws"):
            skip_tests_by_marker(
                items,
                skip_for_c_mqttws,
                "it isn't implemented in the c wrapper with mqtt-ws",
            )

    skip_tests_by_marker(
        items,
        settings.test_module.skip_list,
        "it isn't implemented in the {} wrapper".format(settings.test_module.language),
    )


def set_logger():
    settings.test_module.wrapper_api = adapters.create_adapter(
        settings.test_module.adapter_address, "wrapper"
    )

    def print_and_log(message):
        print(message)
        settings.test_module.wrapper_api.log_message_sync(message)

    adapter_config.logger = print_and_log


def pytest_collection_modifyitems(config, items):
    print("")

    set_transport(config.getoption("--transport"))
    if config.getoption("--local"):
        set_local()
    if config.getoption("--direct-python"):
        set_python_direct()
    set_logger()
    runtime_capabilities.collect_capabilities()
    if config.getoption("--async"):
        set_async()
    add_service_settings()
    adjust_surfaces_for_missing_implementations()
    only_include_scenario_tests(items, config.getoption("--scenario"))
    skip_unsupported_tests(items)

    # make sure the network is connected before starting (this can happen with interrupted runs)
    if settings.test_module.capabilities.v2_connect_group:
        settings.test_module.wrapper_api.network_reconnect_sync()

    if getattr(config, "_origargs", None):
        adapter_config.logger("HORTON: starting run: {}".format(config._origargs))
    elif getattr(config, "invocation_params", None):
        adapter_config.logger(
            "HORTON: starting run: {}".format(config.invocation_params.args)
        )

    if config.getoption("--debug-container"):
        print("Debugging the container.  Removing all timeouts")
        adapter_config.default_api_timeout = 3600
        config._env_timeout = 0

    dump_object(settings)
