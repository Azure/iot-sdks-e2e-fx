# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.test import BaseTestCase


class TestRegistryController(BaseTestCase):
    """RegistryController integration test stubs"""

    def test_registry_connect_put(self):
        """Test case for registry_connect_put

        Connect to registry
        """
        query_string = [('connectionString', 'connectionString_example')]
        response = self.client.open(
            '/registry/connect',
            method='PUT',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_registry_connection_id_disconnect_put(self):
        """Test case for registry_connection_id_disconnect_put

        Disconnect from the registry
        """
        response = self.client.open(
            '/registry/{connectionId}/disconnect/'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_registry_connection_id_module_twin_device_id_module_id_get(self):
        """Test case for registry_connection_id_module_twin_device_id_module_id_get

        gets the module twin for the given deviceid and moduleid
        """
        response = self.client.open(
            '/registry/{connectionId}/moduleTwin/{deviceId}/{moduleId}'.format(connectionId='connectionId_example', deviceId='deviceId_example', moduleId='moduleId_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_registry_connection_id_module_twin_device_id_module_id_patch(self):
        """Test case for registry_connection_id_module_twin_device_id_module_id_patch

        update the module twin for the given deviceId and moduleId
        """
        props = None
        response = self.client.open(
            '/registry/{connectionId}/moduleTwin/{deviceId}/{moduleId}'.format(connectionId='connectionId_example', deviceId='deviceId_example', moduleId='moduleId_example'),
            method='PATCH',
            data=json.dumps(props),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
