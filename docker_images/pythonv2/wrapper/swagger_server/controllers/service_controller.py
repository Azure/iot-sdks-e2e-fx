import connexion
import six

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.event_body import EventBody  # noqa: E501
from swagger_server.models.method_invoke import MethodInvoke  # noqa: E501
from swagger_server import util


def service_connect(connectionString):  # noqa: E501
    """Connect to service

    Connect to the Azure IoTHub service.  More specifically, the SDK saves the connection string that is passed in for future use. # noqa: E501

    :param connectionString: connection string
    :type connectionString: str

    :rtype: ConnectResponse
    """
    return 'do some magic!'


def service_disconnect(connectionId):  # noqa: E501
    """Disconnect from the service

    Disconnects from the Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def service_invoke_device_method(connectionId, deviceId, methodInvokeParameters):  # noqa: E501
    """call the given method on the given device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param methodInvokeParameters: 
    :type methodInvokeParameters: dict | bytes

    :rtype: object
    """
    if connexion.request.is_json:
        methodInvokeParameters = MethodInvoke.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def service_invoke_module_method(connectionId, deviceId, moduleId, methodInvokeParameters):  # noqa: E501
    """call the given method on the given module

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param moduleId: 
    :type moduleId: str
    :param methodInvokeParameters: 
    :type methodInvokeParameters: dict | bytes

    :rtype: object
    """
    if connexion.request.is_json:
        methodInvokeParameters = MethodInvoke.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def service_send_c2d(connectionId, deviceId, eventBody):  # noqa: E501
    """Send a c2d message

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param deviceId: 
    :type deviceId: str
    :param eventBody: 
    :type eventBody: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        eventBody = EventBody.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
