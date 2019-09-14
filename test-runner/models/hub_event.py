# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import json
import base64


class HubEvent:
    def __init__(self):
        self.body = None
        self.properties = []
        self.is_security_message = False

    def convert_to_json(self):
        obj = {"properties": self.properties}

        if isinstance(self.body, str):
            obj["body"] = self.body
            obj["bodyType"] = "string"
        elif isinstance(self.body, dict):
            obj["body"] = self.body
            obj["bodyType"] = "json"
        else:
            obj["body"] = base64.b64encode(self.body).decode("utf-8")
            obj["bodyType"] = "bas64"

        if self.is_security_message:
            obj["isSecurityMessage"] = True

        return obj

    @classmethod
    def create_from_json(cls, json_str):
        obj = json.loads(json_str)
        self = cls()

        self.properties = obj["properties"]

        if "isSecurityMessage" in obj:
            self.is_security_message = obj.is_security_message

        if obj["bodyType"] == "base64":
            self.body = base64.b64decode(obj["body"])
        else:
            self.body = obj["body"]

        return self
