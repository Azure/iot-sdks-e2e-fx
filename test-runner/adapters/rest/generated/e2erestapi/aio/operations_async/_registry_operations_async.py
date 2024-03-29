# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.pipeline import ClientRawResponse
from msrest.exceptions import HttpOperationError

from ... import models


class RegistryOperations:
    """RegistryOperations async operations.

    You should not instantiate directly this class, but create a Client instance that will create it for you and attach it as attribute.

    :param client: Client for service requests.
    :param config: Configuration of service client.
    :param serializer: An object model serializer.
    :param deserializer: An object model deserializer.
    """

    models = models

    def __init__(self, client, config, serializer, deserializer) -> None:

        self._client = client
        self._serialize = serializer
        self._deserialize = deserializer

        self.config = config

    async def connect(
            self, connection_string, *, custom_headers=None, raw=False, **operation_config):
        """Connect to registry.

        Connect to the Azure IoTHub registry.  More specifically, the SDK saves
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
        header_parameters['Accept'] = 'application/json'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.put(url, query_parameters, header_parameters)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('ConnectResponse', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    connect.metadata = {'url': '/registry/connect'}

    async def disconnect(
            self, connection_id, *, custom_headers=None, raw=False, **operation_config):
        """Disconnect from the registry.

        Disconnects from the Azure IoTHub registry.  More specifically, closes
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
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.put(url, query_parameters, header_parameters)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        if raw:
            client_raw_response = ClientRawResponse(None, response)
            return client_raw_response
    disconnect.metadata = {'url': '/registry/{connectionId}/disconnect/'}

    async def get_module_twin(
            self, connection_id, device_id, module_id, *, custom_headers=None, raw=False, **operation_config):
        """gets the module twin for the given deviceid and moduleid.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param module_id:
        :type module_id: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: Twin or ClientRawResponse if raw=true
        :rtype: ~e2erestapi.models.Twin or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.get_module_twin.metadata['url']
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
        header_parameters['Accept'] = 'application/json'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.get(url, query_parameters, header_parameters)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('Twin', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    get_module_twin.metadata = {'url': '/registry/{connectionId}/moduleTwin/{deviceId}/{moduleId}'}

    async def patch_module_twin(
            self, connection_id, device_id, module_id, twin, *, custom_headers=None, raw=False, **operation_config):
        """update the module twin for the given deviceId and moduleId.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param module_id:
        :type module_id: str
        :param twin:
        :type twin: ~e2erestapi.models.Twin
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
        url = self.patch_module_twin.metadata['url']
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
        body_content = self._serialize.body(twin, 'Twin')

        # Construct and send request
        request = self._client.patch(url, query_parameters, header_parameters, body_content)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        if raw:
            client_raw_response = ClientRawResponse(None, response)
            return client_raw_response
    patch_module_twin.metadata = {'url': '/registry/{connectionId}/moduleTwin/{deviceId}/{moduleId}'}

    async def get_device_twin(
            self, connection_id, device_id, *, custom_headers=None, raw=False, **operation_config):
        """gets the device twin for the given deviceid.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param dict custom_headers: headers that will be added to the request
        :param bool raw: returns the direct response alongside the
         deserialized response
        :param operation_config: :ref:`Operation configuration
         overrides<msrest:optionsforoperations>`.
        :return: Twin or ClientRawResponse if raw=true
        :rtype: ~e2erestapi.models.Twin or ~msrest.pipeline.ClientRawResponse
        :raises:
         :class:`HttpOperationError<msrest.exceptions.HttpOperationError>`
        """
        # Construct URL
        url = self.get_device_twin.metadata['url']
        path_format_arguments = {
            'connectionId': self._serialize.url("connection_id", connection_id, 'str'),
            'deviceId': self._serialize.url("device_id", device_id, 'str')
        }
        url = self._client.format_url(url, **path_format_arguments)

        # Construct parameters
        query_parameters = {}

        # Construct headers
        header_parameters = {}
        header_parameters['Accept'] = 'application/json'
        if custom_headers:
            header_parameters.update(custom_headers)

        # Construct and send request
        request = self._client.get(url, query_parameters, header_parameters)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        deserialized = None
        if response.status_code == 200:
            deserialized = self._deserialize('Twin', response)

        if raw:
            client_raw_response = ClientRawResponse(deserialized, response)
            return client_raw_response

        return deserialized
    get_device_twin.metadata = {'url': '/registry/{connectionId}/deviceTwin/{deviceId}'}

    async def patch_device_twin(
            self, connection_id, device_id, twin, *, custom_headers=None, raw=False, **operation_config):
        """update the device twin for the given deviceId.

        :param connection_id: Id for the connection
        :type connection_id: str
        :param device_id:
        :type device_id: str
        :param twin:
        :type twin: ~e2erestapi.models.Twin
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
        url = self.patch_device_twin.metadata['url']
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
        body_content = self._serialize.body(twin, 'Twin')

        # Construct and send request
        request = self._client.patch(url, query_parameters, header_parameters, body_content)
        response = await self._client.async_send(request, stream=False, **operation_config)

        if response.status_code not in [200, 204]:
            raise HttpOperationError(self._deserialize, response)

        if raw:
            client_raw_response = ClientRawResponse(None, response)
            return client_raw_response
    patch_device_twin.metadata = {'url': '/registry/{connectionId}/deviceTwin/{deviceId}'}
