# connectino!/usr/bin/env python

# --------------------------------------------------------------------------
# Deployment types

EDGEHUB_DEPLOYMENT = "edgehub_deplyment"
IOTHUB_DEPLOYMENT = "iothub_deployment"

valid_deployment_types = [EDGEHUB_DEPLOYMENT, IOTHUB_DEPLOYMENT]

# --------------------------------------------------------------------------
# scenario flags

CONNECT_WITH_ENVIRONMENT = "connect_with_environment"
USE_IOTEDGE_GATEWAYHOST = "use_iotedge_gatewayhost"

valid_scenario_flags = [CONNECT_WITH_ENVIRONMENT, USE_IOTEDGE_GATEWAYHOST]

# --------------------------------------------------------------------------
# HortonScenario object

EDGEHUB_MODULE = "edgehub_module"
IOTHUB_MODULE = "iothub_module"
EDGEHUB_MODULE_FI = "edgehub_module_fi"
IOTHUB_MODULE_AND_DEVICE = "iothub_module_and_device"

valid_scenarios = [
    EDGEHUB_MODULE,
    IOTHUB_MODULE,
    EDGEHUB_MODULE_FI,
    IOTHUB_MODULE_AND_DEVICE,
]


class HortonScenario:
    def __init__(self, scenario_name, deployment_type, pytest_markers, scenario_flags):
        self.scenario_name = scenario_name
        self.deployment_type = deployment_type
        self.pytest_markers = pytest_markers
        self.scenario_flags = scenario_flags


scenarios = {
    "edgehub_module": HortonScenario(
        scenario_name=EDGEHUB_MODULE,
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_module_client"],
        scenario_flags=[CONNECT_WITH_ENVIRONMENT, USE_IOTEDGE_GATEWAYHOST],
    ),
    "iothub_module": HortonScenario(
        scenario_name=IOTHUB_MODULE,
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=["testgroup_iothub_module_client"],
        scenario_flags=[],
    ),
    "edgehub_module_fi": HortonScenario(
        scenario_name=EDGEHUB_MODULE_FI,
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_fault_injection"],
        scenario_flags=[CONNECT_WITH_ENVIRONMENT, USE_IOTEDGE_GATEWAYHOST],
    ),
    "iothub_module_and_device": HortonScenario(
        scenario_name=IOTHUB_MODULE_AND_DEVICE,
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=[
            "testgroup_iothub_module_client",
            "testgroup_iothub_device_client",
        ],
        scenario_flags=[],
    ),
}
