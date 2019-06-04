#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


class BaseModuleOrDeviceApi(object):
    def enable_twin(self):
        self.glue.enable_twin()

    def get_twin(self):
        return self.glue.get_twin()

    def patch_twin(self, patch):
        self.glue.send_twin_patch(patch)

    def wait_for_desired_property_patch_async(self):
        return self.pool.apply_async(self.glue.wait_for_desired_property_patch)

    def send_event(self, body):
        self.glue.send_event(body)

    def send_event_async(self, body):
        return self.pool.apply_async(self.glue.send_event, (body,))

    def enable_methods(self):
        self.glue.enable_methods()

    def roundtrip_method_async(
        self, method_name, status_code, request_payload, response_payload
    ):
        class RequestAndResponse(object):
            pass

        request_and_response = RequestAndResponse()
        request_and_response.request_payload = request_payload
        request_and_response.response_payload = response_payload
        request_and_response.status_code = status_code
        return self.pool.apply_async(
            self.glue.roundtrip_method_call, (method_name, request_and_response)
        )
