# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.certificate import Certificate  # noqa: E501
from swagger_server.models.connect_response import ConnectResponse  # noqa: E501
from swagger_server.models.roundtrip_method_call_body import RoundtripMethodCallBody  # noqa: E501
from swagger_server.test import BaseTestCase


class TestModuleController(BaseTestCase):
    """ModuleController integration test stubs"""

    def test_module_connect_from_environment_transport_type_put(self):
        """Test case for module_connect_from_environment_transport_type_put

        Connect to the azure IoT Hub as a module using the environment variables
        """
        response = self.client.open(
            '/module/connectFromEnvironment/{transportType}'.format(transportType='transportType_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connect_transport_type_put(self):
        """Test case for module_connect_transport_type_put

        Connect to the azure IoT Hub as a module
        """
        caCertificate = Certificate()
        query_string = [('connectionString', 'connectionString_example')]
        response = self.client.open(
            '/module/connect/{transportType}'.format(transportType='transportType_example'),
            method='PUT',
            data=json.dumps(caCertificate),
            content_type='application/json',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_device_method_device_id_put(self):
        """Test case for module_connection_id_device_method_device_id_put

        call the given method on the given device
        """
        methodInvokeParameters = None
        response = self.client.open(
            '/module/{connectionId}/deviceMethod/{deviceId}'.format(connectionId='connectionId_example', deviceId='deviceId_example'),
            method='PUT',
            data=json.dumps(methodInvokeParameters),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_disconnect_put(self):
        """Test case for module_connection_id_disconnect_put

        Disconnect the module
        """
        response = self.client.open(
            '/module/{connectionId}/disconnect'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_enable_input_messages_put(self):
        """Test case for module_connection_id_enable_input_messages_put

        Enable input messages
        """
        response = self.client.open(
            '/module/{connectionId}/enableInputMessages'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_enable_methods_put(self):
        """Test case for module_connection_id_enable_methods_put

        Enable methods
        """
        response = self.client.open(
            '/module/{connectionId}/enableMethods'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_enable_twin_put(self):
        """Test case for module_connection_id_enable_twin_put

        Enable module twins
        """
        response = self.client.open(
            '/module/{connectionId}/enableTwin'.format(connectionId='connectionId_example'),
            method='PUT')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_event_put(self):
        """Test case for module_connection_id_event_put

        Send an event
        """
        eventBody = 'eventBody_example'
        response = self.client.open(
            '/module/{connectionId}/event'.format(connectionId='connectionId_example'),
            method='PUT',
            data=json.dumps(eventBody),
            content_type='text/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_input_message_input_name_get(self):
        """Test case for module_connection_id_input_message_input_name_get

        Wait for a message on a module input
        """
        response = self.client.open(
            '/module/{connectionId}/inputMessage/{inputName}'.format(connectionId='connectionId_example', inputName='inputName_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_module_method_device_id_module_id_put(self):
        """Test case for module_connection_id_module_method_device_id_module_id_put

        call the given method on the given module
        """
        methodInvokeParameters = None
        response = self.client.open(
            '/module/{connectionId}/moduleMethod/{deviceId}/{moduleId}'.format(connectionId='connectionId_example', deviceId='deviceId_example', moduleId='moduleId_example'),
            method='PUT',
            data=json.dumps(methodInvokeParameters),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_output_event_output_name_put(self):
        """Test case for module_connection_id_output_event_output_name_put

        Send an event to a module output
        """
        eventBody = 'eventBody_example'
        response = self.client.open(
            '/module/{connectionId}/outputEvent/{outputName}'.format(connectionId='connectionId_example', outputName='outputName_example'),
            method='PUT',
            data=json.dumps(eventBody),
            content_type='text/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_roundtrip_method_call_method_name_put(self):
        """Test case for module_connection_id_roundtrip_method_call_method_name_put

        Wait for a method call, verify the request, and return the response.
        """
        requestAndResponse = RoundtripMethodCallBody()
        response = self.client.open(
            '/module/{connectionId}/roundtripMethodCall/{methodName}'.format(connectionId='connectionId_example', methodName='methodName_example'),
            method='PUT',
            data=json.dumps(requestAndResponse),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_twin_desired_prop_patch_get(self):
        """Test case for module_connection_id_twin_desired_prop_patch_get

        Wait for the next desired property patch
        """
        response = self.client.open(
            '/module/{connectionId}/twinDesiredPropPatch'.format(connectionId='connectionId_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_twin_get(self):
        """Test case for module_connection_id_twin_get

        Get the device twin
        """
        response = self.client.open(
            '/module/{connectionId}/twin'.format(connectionId='connectionId_example'),
            method='GET')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_module_connection_id_twin_patch(self):
        """Test case for module_connection_id_twin_patch

        Updates the device twin
        """
        props = None
        response = self.client.open(
            '/module/{connectionId}/twin'.format(connectionId='connectionId_example'),
            method='PATCH',
            data=json.dumps(props),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
