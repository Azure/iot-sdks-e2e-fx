#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

desired_properties = {"properties": {"desired": {"fake_desired_property": "yes"}}}

reported_properties = {"fake_reported_property": "yes"}

invalid_connection_string = "invalid_connection_string"

bad_connection_id = "bad_connection_id"

method_parameters = {
    "methodName": "fake_method_name",
    "payload": "fake_method_payload",
    "responseTimeoutInSeconds": 15,
}

device_id = "fake_device_id"

module_id = "fake_module_id"

method_name = "fake_method_name"

response_id = "fake_response_id"

method_response_body = {"message": "fake_method_response_body_message"}

status_code = "fake_status_code"

output_name = "fake_output_name"

input_name = "fake_input_name"

event_body = "fake_event_body"

transport = "mqtt"

ca_certificate = "fake_ca_certificate"
