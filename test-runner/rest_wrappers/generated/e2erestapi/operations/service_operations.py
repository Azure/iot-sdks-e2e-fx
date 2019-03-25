# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.pipeline import ClientRawResponse
from msrest.exceptions import HttpOperationError

from .. import models


class ServiceOperations(object):
    """ServiceOperations operations.

    :param client: Client for service requests.
    :param config: Configuration of service client.
    :param serializer: An object model serializer.
    :param deserializer: An object model deserializer.
    """

    models = models

    def __init__(self, client, config, serializer, deserializer):

        self._client = client
        self._serialize = serializer
        self._deserialize = deserializer

        self.config = config

    def connect(
            self, connection_string, custom_headers=None, raw=False, **operation_config):
        """Connect to service.

        Connect to the Azure IoTHub service.  More specifically, the SDK saves
        the connection string that is passed in for future use.

        :param connection_string: connection string
        :type connection_string: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: ConnectResponse or ClientRawResponse if raw=true
        :rtype: ~e2erestapi.models.ConnectResponse or
         ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.connect.metadata['url']

        # Construct parameters
        query_parameters = {}
        query_parameters['connectionString'] = self._serialize.query("connection_string", connection_string, 'str')

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.put(url, query_parameters)
        response = self._client.send(request, header_parameters, stream=False, **operation_config)

        if response.status_code not in [200]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            deserialized = self._deserialize('ConnectResponse', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    connect.metadata = {'url': '/service/connect'}

    def disconnect(
            self, connection_id, custom_headers=None, raw=False, **operation_config):
        """Disconnect from the service.

        Disconnects from the Azure IoTHub service.  More specifically, closes
        all connections and cleans up all resources for the active connection.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: None or ClientRawResponse if raw=true
        :rtype: None or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.disconnect.metadata['url']
        path_format_arguments = {
            'connectionId': self._serialize.url("connection_id", connection_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.put(url, query_parameters)
        response = self._client.send(request, header_parameters, stream=False, **operation_config)

        if response.status_code not in [200]:
            raise HttpOperationError(self._deserialize, response)

        if raw:
            client_raw_response = ClientRawResponse(None, response)
            return client_raw_response
    disconnect.metadata = {'url': '/service/{connectionId}/disconnect/'}

    def invoke_module_method(
            self, connection_id, device_id, module_id, method_invoke_parameters, custom_headers=None, raw=False, **operation_config):
        """call the given method on the given module.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param module_id:
        :type module_id: str
        :param method_invoke_parameters:
        :type method_invoke_parameters: object
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: object or ClientRawResponse if raw=true
        :rtype: object or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.invoke_module_method.metadata['url']
        path_format_arguments = {
            'connectionId': self._serialize.url("connection_id", connection_id, 'str'),
            'deviceId': self._serialize.url("device_id", device_id, 'str'),
            'moduleId': self._serialize.url("module_id", module_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct body
        body_content = self._serialize.body(method_invoke_parameters, 'object')

        # Construct and send request
        request = self._client.put(url, query_parameters)
        response = self._client.send(
            request, header_parameters, body_content, stream=False, **operation_config)

        if response.status_code not in [200]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            deserialized = self._deserialize('object', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    invoke_module_method.metadata = {'url': '/service/{connectionId}/moduleMethod/{deviceId}/{moduleId}'}

    def invoke_device_method(
            self, connection_id, device_id, method_invoke_parameters, custom_headers=None, raw=False, **operation_config):
        """call the given method on the given device.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param method_invoke_parameters:
        :type method_invoke_parameters: object
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: object or ClientRawResponse if raw=true
        :rtype: object or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.invoke_device_method.metadata['url']
        path_format_arguments = {
            'connectionId': self._serialize.url("connection_id", connection_id, 'str'),
            'deviceId': self._serialize.url("device_id", device_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'application/json; charset=utf-8'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct body
        body_content = self._serialize.body(method_invoke_parameters, 'object')

        # Construct and send request
        request = self._client.put(url, query_parameters)
        response = self._client.send(
            request, header_parameters, body_content, stream=False, **operation_config)

        if response.status_code not in [200]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None

        if response.status_code == 200:
            deserialized = self._deserialize('object', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    invoke_device_method.metadata = {'url': '/service/{connectionId}/deviceMethod/{deviceId}'}

    def send_c2d(
            self, connection_id, event_body, custom_headers=None, raw=False, **operation_config):
        """Send a c2d message.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param event_body:
        :type event_body: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: None or ClientRawResponse if raw=true
        :rtype: None or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.send_c2d.metadata['url']
        path_format_arguments = {
            'connectionId': self._serialize.url("connection_id", connection_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}

        # Construct headers
        header_parameters = {}
        header_parameters['Content-Type'] = 'text/json'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct body
        body_content = self._serialize.body(event_body, 'str')

        # Construct and send request
        request = self._client.put(url, query_parameters)
        response = self._client.send(
            request, header_parameters, body_content, stream=False, **operation_config)

        if response.status_code not in [200]:
            raise HttpOperationError(self._deserialize, response)

        if raw:
            client_raw_response = ClientRawResponse(None, response)
            return client_raw_response
    send_c2d.metadata = {'url': '/service/{connectionId}/sendC2d'}
