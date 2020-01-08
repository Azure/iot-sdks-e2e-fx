import connexion
import six

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.twin import Twin  # noqa: E501
from swagger_server import util


def registry_connect(connectionString):  # noqa: E501
    """Connect to registry

    Connect to the Azure IoTHub registry.  More specifically, the SDK saves the connection string that is passed in for future use. # noqa: E501

    :param connectionString: connection string
    :type connectionString: str

    :rtype: ConnectResponse
    """
    return 'do some magic!'


def registry_disconnect(connectionId):  # noqa: E501
    """Disconnect from the registry

    Disconnects from the Azure IoTHub registry.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def registry_get_device_twin(connectionId, deviceId):  # noqa: E501
    """gets the device twin for the given deviceid

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str

    :rtype: Twin
    """
    return 'do some magic!'


def registry_get_module_twin(connectionId, deviceId, moduleId):  # noqa: E501
    """gets the module twin for the given deviceid and moduleid

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param moduleId: 
    :type moduleId: str

    :rtype: Twin
    """
    return 'do some magic!'


def registry_patch_device_twin(connectionId, deviceId, twin):  # noqa: E501
    """update the device twin for the given deviceId

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param twin: 
    :type twin: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        twin = Twin.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def registry_patch_module_twin(connectionId, deviceId, moduleId, twin):  # noqa: E501
    """update the module twin for the given deviceId and moduleId

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param moduleId: 
    :type moduleId: str
    :param twin: 
    :type twin: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        twin = Twin.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
