import connexion
import six

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.roundtrip_method_call_body import RoundtripMethodCallBody  # noqa: E501
from swagger_server import util


def device_connect(transportType, connectionString, caCertificate=None):  # noqa: E501
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


def device_disconnect(connectionId):  # noqa: E501
    """Disconnect the device

    Disconnects from Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def device_enable_c2_d_messages(connectionId):  # noqa: E501
    """Enable c2d messages

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def device_enable_methods(connectionId):  # noqa: E501
    """Enable methods

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    return 'do some magic!'


def device_roundtrip_method_call(connectionId, methodName, requestAndResponse):  # noqa: E501
    """Wait for a method call, verify the request, and return the response.

    This is a workaround to deal with SDKs that only have method call operations that are sync.  This function responds to the method with the payload of this function, and then returns the method parameters.  Real-world implemenatations would never do this, but this is the only same way to write our test code right now (because the method handlers for C, Java, and probably Python all return the method response instead of supporting an async method call) # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param methodName: name of the method to handle
    :type methodName: str
    :param requestAndResponse: 
    :type requestAndResponse: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        requestAndResponse = RoundtripMethodCallBody.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'


def device_send_event(connectionId, eventBody):  # noqa: E501
    """Send an event

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param eventBody: 
    :type eventBody: str

    :rtype: None
    """
    return 'do some magic!'


def device_wait_for_c2d_message(connectionId, inputName):  # noqa: E501
    """Wait for a c2d message

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param inputName: 
    :type inputName: str

    :rtype: str
    """
    return 'do some magic!'
