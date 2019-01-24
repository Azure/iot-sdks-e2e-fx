#!/usr/bin/env python

# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import json
from swagger_server.controllers import module_controller

def log_message(msg):
  if 'message' in msg:
    print(msg['message'])
  else:
    print(str(msg))

def cleanup_resources():
  module_controller.module_glue.cleanup_resources()
