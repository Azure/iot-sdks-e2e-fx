import connexion
import six

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.method_request_response import MethodRequestResponse  # noqa: E501
from swagger_server import util


def device_connect_transport_type_put(transportType, connectionString, caCertificate=None):  # noqa: E501
    """Connect to the azure IoT Hub as a device

     # noqa: E501

    :param transportType: Transport to use
    :type transportType: str
    :param connectionString: connection string
    :type connectionString: str
    :param caCertificate: 
    :type caCertificate: dict | bytes

    :rtype: ConnectResponse
    """
    if connexion.request.is_json:
        caCertificate = Certificate.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def device_connection_id_disconnect_put(connectionId):  # noqa: E501
    """Disconnect the device

    Disconnects from Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def device_connection_id_enable_methods_put(connectionId):  # noqa: E501
    """Enable methods

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def device_connection_id_method_request_method_name_get(connectionId, methodName):  # noqa: E501
    """Wait for a method call with the given name

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param methodName: 
    :type methodName: str

    :rtype: MethodRequestResponse
    """
    return 'do some magic!'


def device_connection_id_method_response_response_id_status_code_put(connectionId, responseId, statusCode, responseBody):  # noqa: E501
    """Respond to the method call with the given name

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param responseId: 
    :type responseId: str
    :param statusCode: 
    :type statusCode: str
    :param responseBody: 
    :type responseBody: 

    :rtype: None
    """
    return 'do some magic!'
