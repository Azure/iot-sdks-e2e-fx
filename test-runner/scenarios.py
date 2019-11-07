# --------------------------------------------------------------------------
# Deployment types

EDGEHUB_DEPLOYMENT = "edgehub_deplyment"
IOTHUB_DEPLOYMENT = "iothub_deployment"

valid_deployment_types = [EDGEHUB_DEPLOYMENT, IOTHUB_DEPLOYMENT]

# --------------------------------------------------------------------------
# HortonScenario object

# BKTODO: this class can eventually become empty

EDGEHUB_MODULE = "edgehub_module"
IOTHUB_MODULE = "iothub_module"
IOTHUB_DEVICE = "iothub_device"
EDGEHUB_MODULE_FI = "edgehub_module_fi"
IOTHUB_MODULE_AND_DEVICE = "iothub_module_and_device"

valid_scenarios = [
    EDGEHUB_MODULE,
    IOTHUB_MODULE,
    IOTHUB_DEVICE,
    EDGEHUB_MODULE_FI,
    IOTHUB_MODULE_AND_DEVICE,
]


class HortonScenario:
    def __init__(self, scenario_name, deployment_type, pytest_markers):
        self.scenario_name = scenario_name
        self.deployment_type = deployment_type
        self.pytest_markers = pytest_markers


scenarios = {
    "edgehub_module": HortonScenario(
        scenario_name=EDGEHUB_MODULE,
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_module_client"],
    ),
    "iothub_module": HortonScenario(
        scenario_name=IOTHUB_MODULE,
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=["testgroup_iothub_module_client"],
    ),
    "edgehub_module_fi": HortonScenario(
        scenario_name=EDGEHUB_MODULE_FI,
        deployment_type=EDGEHUB_DEPLOYMENT,
        pytest_markers=["testgroup_edgehub_fault_injection"],
    ),
    "iothub_module_and_device": HortonScenario(
        scenario_name=IOTHUB_MODULE_AND_DEVICE,
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=[
            "testgroup_iothub_module_client",
            "testgroup_iothub_device_client",
        ],
    ),
    "iothub_device": HortonScenario(
        scenario_name=IOTHUB_DEVICE,
        deployment_type=IOTHUB_DEPLOYMENT,
        pytest_markers=["testgroup_iothub_device_client"],
    ),
}
