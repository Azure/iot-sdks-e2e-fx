#!/usr/bin/env python

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


class HortonScenario:
    def __init__(self, deployment_type, pytest_markers, scenario_flags):
        self.deployment_type = deployment_type
        self.pytest_markers = pytest_markers
        self.scenario_flags = scenario_flags


scenarios = {
    "edgehub_module": HortonScenario(
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_module_client"],
        scenario_flags=[CONNECT_WITH_ENVIRONMENT, USE_IOTEDGE_GATEWAYHOST],
    ),
    "iothub_module": HortonScenario(
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=["testgroup_iothub_module_client"], scenario_flags=[]
    ),
    "edgehub_module_fi": HortonScenario(
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_fault_injection"],
        scenario_flags=[CONNECT_WITH_ENVIRONMENT, USE_IOTEDGE_GATEWAYHOST],
    ),
}
