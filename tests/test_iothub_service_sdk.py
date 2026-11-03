# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

from unittest.mock import Mock, call

import pytest
from azure.core.exceptions import (
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from azure.core.pipeline.transport import HttpResponse
from azure.iot.hub import models

import iothub_service_helper as service_helper
from adapters.direct_azure_rest.direct_service_api import _retry_on_transient
from adapters.direct_azure_rest.amqp_service_client import AmqpServiceClient


@pytest.fixture
def http_error():
    def create_error(status_code):
        response = Mock(spec=HttpResponse)
        response.status_code = status_code
        response.reason = "service response"
        response.headers = {}
        response.text.return_value = '{"Message": "service detail"}'
        return HttpResponseError(message="request failed", response=response)

    return create_error


@pytest.fixture(autouse=True)
def sleep(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(service_helper.time, "sleep", mock)
    return mock


def test_service_client_and_model_compatibility():
    helper = service_helper.IoTHubServiceHelper(
        "HostName=test.azure-devices.net;"
        "SharedAccessKeyName=iothubowner;SharedAccessKey=dGVzdC1rZXk="
    )
    assert callable(helper.registry_manager.protocol.devices.create_or_update_identity)
    assert callable(helper.registry_manager.protocol.modules.create_or_update_identity)
    assert callable(helper.configuration_manager.apply_configuration_on_edge_device)
    patch = {"desired": {"example": "value"}}
    assert models.Twin.from_dict({"properties": patch}).as_dict()["properties"] == patch
    assert callable(AmqpServiceClient.send_to_device)


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_deploy_retries_http_errors(http_error, status_code, sleep):
    operation = Mock(side_effect=[http_error(status_code), "result"])
    assert service_helper._retry_transient(operation) == "result"
    assert operation.call_count == 2
    sleep.assert_called_once_with(2)


@pytest.mark.parametrize("error_type", [ServiceRequestError, ServiceResponseError])
def test_deploy_retries_transport_errors(error_type, sleep):
    error = error_type("connection dropped")
    operation = Mock(side_effect=[error, error, "result"])
    assert service_helper._retry_transient(operation) == "result"
    assert operation.call_count == 3
    assert sleep.call_args_list == [call(2), call(4)]


@pytest.mark.parametrize("status_code", [400, 401, 403, 404])
def test_deploy_preserves_http_error_and_service_detail(http_error, status_code, sleep):
    error = http_error(status_code)
    operation = Mock(side_effect=error)
    with pytest.raises(HttpResponseError) as caught:
        service_helper._retry_transient(operation)
    assert caught.value is error
    assert "service detail" in str(caught.value)
    operation.assert_called_once_with()
    sleep.assert_not_called()


@pytest.mark.parametrize("status_code", [404, 503])
def test_method_invocation_retries_http_errors(http_error, status_code, sleep):
    operation = Mock(side_effect=[http_error(status_code), "result"])
    assert _retry_on_transient(operation) == "result"
    assert operation.call_count == 2
    sleep.assert_called_once_with(2)


@pytest.mark.parametrize("status_code", [400, 401, 403])
def test_method_invocation_does_not_retry_other_errors(http_error, status_code, sleep):
    error = http_error(status_code)
    operation = Mock(side_effect=error)
    with pytest.raises(HttpResponseError) as caught:
        _retry_on_transient(operation)
    assert caught.value is error
    operation.assert_called_once_with()
    sleep.assert_not_called()


@pytest.mark.parametrize(
    "retry, attempts",
    [(service_helper._retry_transient, 5), (_retry_on_transient, 3)],
)
def test_retry_exhaustion_preserves_error(http_error, retry, attempts, sleep):
    error = http_error(503)
    operation = Mock(side_effect=error)
    with pytest.raises(HttpResponseError) as caught:
        retry(operation)
    assert caught.value is error
    assert operation.call_count == attempts
    assert sleep.call_count == attempts - 1


@pytest.mark.parametrize("is_module", [False, True])
def test_create_identity_after_not_found(http_error, is_module):
    helper = object.__new__(service_helper.IoTHubServiceHelper)
    helper.registry_manager = Mock()
    if is_module:
        helper.registry_manager.get_module.side_effect = http_error(404)
        operation = helper.registry_manager.protocol.modules.create_or_update_identity
        helper.create_device_module("device", "module")
        device_id, module_id, identity = operation.call_args.args
        assert (device_id, module_id) == ("device", "module")
        assert identity.module_id == "module"
    else:
        helper.registry_manager.get_device.side_effect = http_error(404)
        operation = helper.registry_manager.protocol.devices.create_or_update_identity
        helper.create_device("device")
        device_id, identity = operation.call_args.args
        assert device_id == "device"
    assert identity.device_id == "device"


@pytest.mark.parametrize("is_module", [False, True])
def test_delete_not_found_returns_false(http_error, is_module):
    helper = object.__new__(service_helper.IoTHubServiceHelper)
    helper.registry_manager = Mock()
    if is_module:
        helper.registry_manager.delete_module.side_effect = http_error(404)
        assert helper.try_delete_module("device", "module") is False
    else:
        helper.registry_manager.delete_device.side_effect = http_error(404)
        assert helper.try_delete_device("device") is False
