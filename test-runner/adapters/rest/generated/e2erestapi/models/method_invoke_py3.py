# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.serialization import Model


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

    def __init__(self, *, method_name: str=None, payload=None, response_timeout_in_seconds: int=None, connect_timeout_in_seconds: int=None, **kwargs) -> None:
        super(MethodInvoke, self).__init__(**kwargs)
        self.method_name = method_name
        self.payload = payload
        self.response_timeout_in_seconds = response_timeout_in_seconds
        self.connect_timeout_in_seconds = connect_timeout_in_seconds
