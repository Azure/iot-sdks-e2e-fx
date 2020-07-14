# coding=utf-8
# --------------------------------------------------------------------------
# Code generated by Microsoft (R) AutoRest Code Generator.
# Changes may cause incorrect behavior and will be lost if the code is
# regenerated.
# --------------------------------------------------------------------------

from msrest.service_client import SDKClient
from msrest import Serializer, Deserializer

from ._configuration import AzureIOTEndToEndTestWrapperRestApiConfiguration
from msrest.exceptions import HttpOperationError
from .operations import SystemOperations
from .operations import ControlOperations
from .operations import DeviceOperations
from .operations import ModuleOperations
from .operations import ServiceOperations
from .operations import RegistryOperations
from . import models


class AzureIOTEndToEndTestWrapperRestApi(SDKClient):
    """AzureIOTEndToEndTestWrapperRestApi

    :ivar config: Configuration for client.
    :vartype config: AzureIOTEndToEndTestWrapperRestApiConfiguration

    :ivar system: System operations
    :vartype system: e2erestapi.operations.SystemOperations
    :ivar control: Control operations
    :vartype control: e2erestapi.operations.ControlOperations
    :ivar device: Device operations
    :vartype device: e2erestapi.operations.DeviceOperations
    :ivar module: Module operations
    :vartype module: e2erestapi.operations.ModuleOperations
    :ivar service: Service operations
    :vartype service: e2erestapi.operations.ServiceOperations
    :ivar registry: Registry operations
    :vartype registry: e2erestapi.operations.RegistryOperations

    :param str base_url: Service URL
    """

    def __init__(
            self, base_url=None):

        self.config = AzureIOTEndToEndTestWrapperRestApiConfiguration(base_url)
        super(AzureIOTEndToEndTestWrapperRestApi, self).__init__(None, self.config)

        client_models = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
        self.api_version = '1.0.0'
        self._serialize = Serializer(client_models)
        self._deserialize = Deserializer(client_models)

        self.system = SystemOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.control = ControlOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.device = DeviceOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.module = ModuleOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.service = ServiceOperations(
            self._client, self.config, self._serialize, self._deserialize)
        self.registry = RegistryOperations(
            self._client, self.config, self._serialize, self._deserialize)
