import connexion
import six

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.event_body import EventBody  # noqa: E501
from swagger_server.models.method_invoke import MethodInvoke  # noqa: E501
from swagger_server.models.method_request_and_response import MethodRequestAndResponse  # noqa: E501
from swagger_server.models.twin import Twin  # noqa: E501
from swagger_server import util

# added 3 lines in merge
import json
from module_glue import ModuleGlue

module_glue = ModuleGlue()


def module_connect(transportType, connectionString, caCertificate=None):  # noqa: E501
    """Connect to the azure IoT Hub as a module

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
    return module_glue.connect(transportType, connectionString, caCertificate)


def module_connect2(connectionId):  # noqa: E501
    """Connect the module

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.connect2(connectionId)


def module_connect_from_environment(transportType):  # noqa: E501
    """Connect to the azure IoT Hub as a module using the environment variables

     # noqa: E501

    :param transportType: Transport to use
    :type transportType: str

    :rtype: ConnectResponse
    """
    # changed from return 'do some magic!'
    return module_glue.connect_from_environment(transportType)


def module_create_from_connection_string(transportType, connectionString, caCertificate=None):  # noqa: E501
    """Create a module client from a connection string

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
    return module_glue.create_from_connection_string(
        transportType, connectionString, caCertificate
    )


def module_create_from_environment(transportType):  # noqa: E501
    """Create a module client using the EdgeHub environment

     # noqa: E501

    :param transportType: Transport to use
    :type transportType: str

    :rtype: ConnectResponse
    """
    # changed from return 'do some magic!'
    return module_glue.create_from_environment(transportType)


def module_create_from_x509(transportType, X509):  # noqa: E501
    """Create a module client from X509 credentials

     # noqa: E501

    :param transportType: Transport to use
    :type transportType: str
    :param X509:
    :type X509:

    :rtype: ConnectResponse
    """
    # changed from return 'do some magic!'
    return module_glue.crate_from_x509(transportType, X509)


def module_destroy(connectionId):  # noqa: E501
    """Disonnect and destroy the module client

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.destroy(connectionId)


def module_disconnect(connectionId):  # noqa: E501
    """Disconnect the module

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.disconnect(connectionId)


def module_disconnect2(connectionId):  # noqa: E501
    """Disonnect the module

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.disconnect2(connectionId)


def module_enable_input_messages(connectionId):  # noqa: E501
    """Enable input messages

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.enable_input_messages(connectionId)


def module_enable_methods(connectionId):  # noqa: E501
    """Enable methods

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.enable_methods(connectionId)


def module_enable_twin(connectionId):  # noqa: E501
    """Enable module twins

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.enable_twin(connectionId)


def module_get_connection_status(connectionId):  # noqa: E501
    """get the current connection status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: str
    """
    # changed from return 'do some magic!'
    return json.dumps(module_glue.get_connection_status(connectionId))


def module_get_twin(connectionId):  # noqa: E501
    """Get the device twin

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: Twin
    """
    # changed from return 'do some magic!'
    return module_glue.get_twin(connectionId)


def module_invoke_device_method(connectionId, deviceId, methodInvokeParameters):  # noqa: E501
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
    # changed from return 'do some magic!'
    return module_glue.invoke_device_method(connectionId, deviceId, methodInvokeParameters)


def module_invoke_module_method(connectionId, deviceId, moduleId, methodInvokeParameters):  # noqa: E501
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
    # changed from return 'do some magic!'
    return module_glue.invoke_module_method(
        connectionId, deviceId, moduleId, methodInvokeParameters
    )


def module_patch_twin(connectionId, twin):  # noqa: E501
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
    return module_glue.send_twin_patch(connectionId, twin)


def module_reconnect(connectionId, forceRenewPassword=None):  # noqa: E501
    """Reconnect the module

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param forceRenewPassword: True to force SAS renewal
    :type forceRenewPassword: bool

    :rtype: None
    """
    # changed from return 'do some magic!'
    module_glue.reconnect(forceRenewPassword)


def module_send_event(connectionId, eventBody):  # noqa: E501
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
    module_glue.send_event(connectionId, eventBody)


def module_send_output_event(connectionId, outputName, eventBody):  # noqa: E501
    """Send an event to a module output

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param outputName:
    :type outputName: str
    :param eventBody:
    :type eventBody: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        eventBody = EventBody.from_dict(connexion.request.get_json())  # noqa: E501
    # changed from return 'do some magic!'
    module_glue.send_output_event(connectionId, outputName, eventBody)


def module_wait_for_connection_status_change(connectionId, connectionStatus):  # noqa: E501
    """wait for the current connection status to change and return the changed status

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param connectionStatus: Desired connection status
    :type connectionStatus: str

    :rtype: str
    """
    # changed from return 'do some magic!'
    return json.dumps(module_glue.wait_for_connection_status_change(connectionId, connectionStatus))


def module_wait_for_desired_properties_patch(connectionId):  # noqa: E501
    """Wait for the next desired property patch

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str

    :rtype: Twin
    """
    # changed from return 'do some magic!'
    return module_glue.wait_for_desired_property_patch(connectionId)


def module_wait_for_input_message(connectionId, inputName):  # noqa: E501
    """Wait for a message on a module input

     # noqa: E501

    :param connectionId: Id for the connection
    :type connectionId: str
    :param inputName:
    :type inputName: str

    :rtype: EventBody
    """
    # changed from return 'do some magic!'
    return module_glue.wait_for_input_message(connectionId, inputName)


def module_wait_for_method_and_return_response(connectionId, methodName, requestAndResponse):  # noqa: E501
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
    return module_glue.wait_for_method_and_return_response(connectionId, methodName, requestAndResponse)
