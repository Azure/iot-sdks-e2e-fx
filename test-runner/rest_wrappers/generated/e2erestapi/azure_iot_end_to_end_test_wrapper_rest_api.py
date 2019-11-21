# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.service_client import ServiceClient
from msrest import Configuration, Serializer, Deserializer
from .version import VERSION
from msrest.exceptions import HttpOperationError
from .operations.wrapper_operations import WrapperOperations
from .operations.registry_operations import RegistryOperations
from .operations.module_operations import ModuleOperations
from .operations.service_operations import ServiceOperations
from .operations.device_operations import DeviceOperations
from .operations.net_operations import NetOperations
from . import models


class AzureIOTEndToEndTestWrapperRestApiConfiguration(Configuration):
    """Configuration for AzureIOTEndToEndTestWrapperRestApi
    Note that all parameters used to create this instance are saved as instance
    attributes.

    :param str base_url: Service URL
    """

    def __init__(
            self, base_url=None):

        if not base_url:
            base_url = 'http://localhost'

        super(AzureIOTEndToEndTestWrapperRestApiConfiguration, self).__init__(base_url)

        self.add_user_agent('azureiotendtoendtestwrapperrestapi/{}'.format(VERSION))


class AzureIOTEndToEndTestWrapperRestApi(object):
    """REST API definition for End-to-end testing of the Azure IoT SDKs.  All SDK APIs that are tested by our E2E tests need to be defined in this file.  This file takes some liberties with the API definitions.  In particular, response schemas are undefined, and error responses are also undefined.

    :ivar config: Configuration for client.
    :vartype config: AzureIOTEndToEndTestWrapperRestApiConfiguration

    :ivar wrapper: Wrapper operations
    :vartype wrapper: e2erestapi.operations.WrapperOperations
    :ivar registry: Registry operations
    :vartype registry: e2erestapi.operations.RegistryOperations
    :ivar module: Module operations
    :vartype module: e2erestapi.operations.ModuleOperations
    :ivar service: Service operations
    :vartype service: e2erestapi.operations.ServiceOperations
    :ivar device: Device operations
    :vartype device: e2erestapi.operations.DeviceOperations
    :ivar net: Net operations
    :vartype net: e2erestapi.operations.NetOperations

    :param str base_url: Service URL
    """

    def __init__(
            self, base_url=None):

        self.config = AzureIOTEndToEndTestWrapperRestApiConfiguration(base_url)
        self._client = ServiceClient(None, self.config)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = '1.0.0'
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        self.wrapper = WrapperOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.registry = RegistryOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.module = ModuleOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.service = ServiceOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.device = DeviceOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.net = NetOperations(
            self._client, self.config, self._serialize, self._deserialize)
