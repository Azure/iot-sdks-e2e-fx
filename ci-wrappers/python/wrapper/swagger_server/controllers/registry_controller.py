import connexion
import six

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server import util


def registry_connect_put(connectionString):  # noqa: E501
    """Connect to registry

    Connect to the Azure IoTHub registry.  More specifically, the SDK saves the connection string that is passed in for future use. # noqa: E501

    :param connectionString: Service connection string
    :type connectionString: str

    :rtype: ConnectResponse
    """
    return 'do some magic!'


def registry_connection_id_disconnect_put(connectionId):  # noqa: E501
    """Disconnect from the registry

    Disconnects from the Azure IoTHub registry.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def registry_connection_id_module_twin_device_id_module_id_get(connectionId, deviceId, moduleId):  # noqa: E501
    """gets the module twin for the given deviceid and moduleid

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param moduleId: 
    :type moduleId: str

    :rtype: object
    """
    return 'do some magic!'


def registry_connection_id_module_twin_device_id_module_id_patch(connectionId, deviceId, moduleId, props):  # noqa: E501
    """update the module twin for the given deviceId and moduleId

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param moduleId: 
    :type moduleId: str
    :param props: 
    :type props: 

    :rtype: None
    """
    return 'do some magic!'
