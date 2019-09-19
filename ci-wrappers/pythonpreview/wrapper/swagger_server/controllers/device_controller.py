import connexion
import six

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.roundtrip_method_call_body import RoundtripMethodCallBody  # noqa: E501
from swagger_server import util

# Added 2 lines in merge
from device_glue import DeviceGlue
device_glue = DeviceGlue()

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
    # changed from return 'do some magic!'
    return device_glue.connect(transportType, connectionString, caCertificate)


def device_disconnect(connectionId):  # noqa: E501
    """Disconnect the device

    Disconnects from Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.disconnect(connectionId)


def device_enable_c2d_messages(connectionId):  # noqa: E501
    """Enable c2d messages

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.enable_c2d(connectionId)


def device_enable_methods(connectionId):  # noqa: E501
    """Enable methods

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.enable_methods(connectionId)


def device_enable_twin(connectionId):  # noqa: E501
    """Enable device twins

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.enable_twin(connectionId)


def device_get_connection_status(connectionId):  # noqa: E501
    """get the current connection status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: object
    """
    return 'do some magic!'


def device_get_twin(connectionId):  # noqa: E501
    """Get the device twin

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: object
    """
    # changed from return 'do some magic!'
    return device_glue.get_twin(connectionId)


def device_patch_twin(connectionId, props):  # noqa: E501
    """Updates the device twin

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param props: 
    :type props: 

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.send_twin_patch(connectionId, props)


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
    # changed from return 'do some magic!'
    return device_glue.roundtrip_method_call(
        connectionId, methodName, requestAndResponse
    )


def device_send_event(connectionId, eventBody):  # noqa: E501
    """Send an event

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param eventBody: 
    :type eventBody: 

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.send_event(connectionId, eventBody)


def device_wait_for_c2d_message(connectionId):  # noqa: E501
    """Wait for a c2d message

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: str
    """
    # changed from return 'do some magic!'
    return device_glue.wait_for_c2d_message(connectionId)


def device_wait_for_connection_status_change(connectionId):  # noqa: E501
    """wait for the current connection status to change and return the changed status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: object
    """
    return 'do some magic!'


def device_wait_for_desired_properties_patch(connectionId):  # noqa: E501
    """Wait for the next desired property patch

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: object
    """
    # changed from return 'do some magic!'
    return device_glue.wait_for_desired_property_patch(connectionId)
