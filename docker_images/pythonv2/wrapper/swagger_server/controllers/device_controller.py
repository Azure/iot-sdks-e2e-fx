import connexion
import six

from swagger_server.models.blob_storage_info import BlobStorageInfo  # noqa: E501
from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.event_body import EventBody  # noqa: E501
from swagger_server.models.method_request_and_response import MethodRequestAndResponse  # noqa: E501
from swagger_server.models.twin import Twin  # noqa: E501
from swagger_server import util

# Added 3 lines in merge
import json
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


def device_connect2(connectionId):  # noqa: E501
    """Connect the device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.connect2(connectionId)


def device_create_from_connection_string(transportType, connectionString, caCertificate=None):  # noqa: E501
    """Create a device client from a connection string

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
    return device_glue.create_from_connection_string(
        transportType, connectionString, caCertificate
    )


def device_create_from_x509(transportType, X509):  # noqa: E501
    """Create a device client from X509 credentials

     # noqa: E501

    :param transportType: Transport to use
    :type transportType: str
    :param X509: 
    :type X509: 

    :rtype: ConnectResponse
    """
    # changed from return 'do some magic!'
    return device_glue.create_from_x509(transportType, X509)


def device_destroy(connectionId):  # noqa: E501
    """Disconnect and destroy the device client

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.destroy(connectionId)


def device_disconnect(connectionId):  # noqa: E501
    """Disconnect the device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.disconnect(connectionId)


def device_disconnect2(connectionId):  # noqa: E501
    """Disconnect the device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.disconnect2(connectionId)


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

    :rtype: str
    """
    # changed from return 'do some magic!'
    return json.dumps(device_glue.get_connection_status(connectionId))


def device_get_storage_info_for_blob(connectionId, blobName):  # noqa: E501
    """Get storage info for uploading into blob storage

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param blobName: name of blob
    :type blobName: str

    :rtype: BlobStorageInfo
    """
    # changed from return 'do some magic!'
    return device_glue.get_storage_info_for_blob(connectionId, blobName)


def device_get_twin(connectionId):  # noqa: E501
    """Get the device twin

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: Twin
    """
    # changed from return 'do some magic!'
    return device_glue.get_twin(connectionId)

def device_notify_blob_upload_status(connectionId, correlationId, isSuccess, statusCode, statusDescription):  # noqa: E501
    """notify iothub about blob upload status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param correlationId: correlation id for blob upload
    :type correlationId: str
    :param isSuccess: True if blob upload was successful
    :type isSuccess: bool
    :param statusCode: status code for blob upload
    :type statusCode: str
    :param statusDescription: human readable descripton of the status for blob upload
    :type statusDescription: str

    :rtype: None
    """
    return 'do some magic!'


def device_patch_twin(connectionId, twin):  # noqa: E501
    """Updates the device twin

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param twin: 
    :type twin: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        twin = Twin.from_dict(connexion.request.get_json())  # noqa: E501
    # changed from return 'do some magic!'
    device_glue.send_twin_patch(connectionId, twin)


def device_reconnect(connectionId, forceRenewPassword=None):  # noqa: E501
    """Reconnect the device

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param forceRenewPassword: True to force SAS renewal
    :type forceRenewPassword: bool

    :rtype: None
    """
    # changed from return 'do some magic!'
    device_glue.reconnect(connectionId, forceRenewPassword)


def device_send_event(connectionId, eventBody):  # noqa: E501
    """Send an event

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param eventBody: 
    :type eventBody: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        eventBody = EventBody.from_dict(connexion.request.get_json())  # noqa: E501
    # changed from return 'do some magic!'
    device_glue.send_event(connectionId, eventBody)


def device_wait_for_c2d_message(connectionId):  # noqa: E501
    """Wait for a c2d message

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: EventBody
    """
    # changed from return 'do some magic!'
    return device_glue.wait_for_c2d_message(connectionId)


def device_wait_for_connection_status_change(connectionId, connectionStatus):  # noqa: E501
    """wait for the current connection status to change and return the changed status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param connectionStatus: Desired connection status
    :type connectionStatus: str

    :rtype: str
    """
    # changed from return 'do some magic!'
    return json.dumps(
        device_glue.wait_for_connection_status_change(connectionId, connectionStatus)
    )


def device_wait_for_desired_properties_patch(connectionId):  # noqa: E501
    """Wait for the next desired property patch

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: Twin
    """
    # changed from return 'do some magic!'
    return device_glue.wait_for_desired_property_patch(connectionId)


def device_wait_for_method_and_return_response(connectionId, methodName, requestAndResponse):  # noqa: E501
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
        requestAndResponse = MethodRequestAndResponse.from_dict(connexion.request.get_json())  # noqa: E501
    # changed from return 'do some magic!'
    return device_glue.wait_for_method_and_return_response(
        connectionId, methodName, requestAndResponse
    )