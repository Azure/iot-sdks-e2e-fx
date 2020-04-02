# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


class Certificate(Model):
    """certificate in the body of a message.

    :param cert: unique identifier for this connection
    :type cert: str
    """

    _attribute_map = {
        'cert': {'key': 'cert', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(Certificate, self).__init__(**kwargs)
        self.cert = kwargs.get('cert', None)


class ConnectResponse(Model):
    """result of a connection to a service, device, or module client.

    :param connection_id: unique identifier for this connection
    :type connection_id: str
    """

    _attribute_map = {
        'connection_id': {'key': 'connectionId', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(ConnectResponse, self).__init__(**kwargs)
        self.connection_id = kwargs.get('connection_id', None)


class EventBody(Model):
    """body for an invoming or outgoing event or message.

    :param body: payload to send to the method
    :type body: object
    :param horton_flags: flags used by horton
    :type horton_flags: object
    :param attributes: Message attributes
    :type attributes: object
    """

    _attribute_map = {
        'body': {'key': 'body', 'type': 'object'},
        'horton_flags': {'key': 'horton_flags', 'type': 'object'},
        'attributes': {'key': 'attributes', 'type': 'object'},
    }

    def __init__(self, **kwargs):
        super(EventBody, self).__init__(**kwargs)
        self.body = kwargs.get('body', None)
        self.horton_flags = kwargs.get('horton_flags', None)
        self.attributes = kwargs.get('attributes', None)


class LogMessage(Model):
    """message from the test script to output to the log.

    :param message: text of message
    :type message: str
    """

    _attribute_map = {
        'message': {'key': 'message', 'type': 'str'},
    }

    def __init__(self, **kwargs):
        super(LogMessage, self).__init__(**kwargs)
        self.message = kwargs.get('message', None)


class MethodInvoke(Model):
    """parameters used to invoke a method.

    :param method_name: name of method to invoke
    :type method_name: str
    :param payload: payload to send to the method
    :type payload: object
    :param response_timeout_in_seconds: number of seconds to wait for a
     response
    :type response_timeout_in_seconds: int
    :param connect_timeout_in_seconds: number of seconds to wait for the
     module to connect
    :type connect_timeout_in_seconds: int
    """

    _attribute_map = {
        'method_name': {'key': 'methodName', 'type': 'str'},
        'payload': {'key': 'payload', 'type': 'object'},
        'response_timeout_in_seconds': {'key': 'responseTimeoutInSeconds', 'type': 'int'},
        'connect_timeout_in_seconds': {'key': 'connectTimeoutInSeconds', 'type': 'int'},
    }

    def __init__(self, **kwargs):
        super(MethodInvoke, self).__init__(**kwargs)
        self.method_name = kwargs.get('method_name', None)
        self.payload = kwargs.get('payload', None)
        self.response_timeout_in_seconds = kwargs.get('response_timeout_in_seconds', None)
        self.connect_timeout_in_seconds = kwargs.get('connect_timeout_in_seconds', None)


class MethodRequestAndResponse(Model):
    """parameters and response for a sync method call.

    :param request_payload: payload for the request that arrived from the
     service.  Used to verify that the correct request arrived.
    :type request_payload: object
    :param response_payload: payload for the response to return to the
     service.  Used to verify that the correct request arrived.
    :type response_payload: object
    :param status_code: status code to return to the service
    :type status_code: int
    """

    _attribute_map = {
        'request_payload': {'key': 'requestPayload', 'type': 'object'},
        'response_payload': {'key': 'responsePayload', 'type': 'object'},
        'status_code': {'key': 'statusCode', 'type': 'int'},
    }

    def __init__(self, **kwargs):
        super(MethodRequestAndResponse, self).__init__(**kwargs)
        self.request_payload = kwargs.get('request_payload', None)
        self.response_payload = kwargs.get('response_payload', None)
        self.status_code = kwargs.get('status_code', None)


class Twin(Model):
    """device twin or module twin.

    :param desired: desired properties
    :type desired: object
    :param reported: reported properties
    :type reported: object
    """

    _attribute_map = {
        'desired': {'key': 'desired', 'type': 'object'},
        'reported': {'key': 'reported', 'type': 'object'},
    }

    def __init__(self, **kwargs):
        super(Twin, self).__init__(**kwargs)
        self.desired = kwargs.get('desired', None)
        self.reported = kwargs.get('reported', None)
