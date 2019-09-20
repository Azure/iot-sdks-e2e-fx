# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from swagger_server.iothub_client import IoTHubModuleClient, IoTHubTransportProvider, IoTHubMessage, IoTHubMessageDispositionResult, DeviceMethodReturnValue
from swagger_server.models.connect_response import ConnectResponse
import threading
import json

def transport_name_to_type(transport_name):
  return {
    'mqtt': IoTHubTransportProvider.MQTT,
    'mqttws': IoTHubTransportProvider.MQTT_WS,
    'amqp': IoTHubTransportProvider.AMQP,
    'amqpws': IoTHubTransportProvider.AMQP_WS,
    'http': IoTHubTransportProvider.HTTP
  }[transport_name]

class TwinCallbackContext:
  def __init__(self):
    self.event = threading.Event()
    self.latest_payload = {}
    self.current_complete_twin = {}

class MessageCallbackContext:
  def __init__(self):
    self.event = threading.Event()
    self.response = ""

class MethodInvokeContext:
  def __init__(self):
    self.event = threading.Event()
    self.payload = ""

class MethodCallbackContext:
  def __init__(self, expected_method_name, expected_request_payload, response, status_code):
    self.event = threading.Event()
    self.expected_method_name = expected_method_name
    self.actual_method_name = ""
    self.expected_request_payload = expected_request_payload
    self.actual_request_payload = ""
    self.response = response
    self.status_code = status_code

def patch_twin(prev_complete_twin, patch):
  j = prev_complete_twin
  if "desired" in patch:
    j["desired"] = patch["desired"]
  else:
    j["desired"] = patch
  return j

def twin_key(connection_id):
  return connection_id + "_twin"

def send_confirmation_callback(message, result, user_context):
  print('send confirmation callback complete ' + str(result))
  user_context.set()

def device_twin_callback(update_state, payload, user_context):
  print("device twin callback - state = {}".format(update_state))
  print(payload)
  payload = json.loads(payload)
  if (update_state == "COMPLETE"):
    print('device twin callback - COMPLETE')
    user_context.current_complete_twin = payload
  else:
    print('device twin callback - PARTIAL')
    user_context.latest_payload = payload
    user_context.current_complete_twin = patch_twin(user_context.current_complete_twin, user_context.latest_payload)
  user_context.event.set()

def reported_state_callback(status_code, user_context):
  print('reported state callback complete ' + str(status_code))
  user_context.set()

def receive_message_callback(message, user_context):
  print('received message callback')
  msg_str = message.get_string()
  if (msg_str):
    user_context.response = msg_str
  else:
    try:
      msg_byte_arr = message.get_bytearray()
    except:
      msg_byte_arr = "WARNING: get_bytearray threw exception"

    user_context.response = msg_byte_arr.decode("utf-8")
    user_context.event.set()
    return IoTHubMessageDispositionResult.ACCEPTED

def method_invoke_callback(response, user_context):
  print('method invoke callback complete')
  user_context.payload = response.responsePayload
  user_context.event.set()

def module_method_callback(method_name, payload, user_context):
  result = DeviceMethodReturnValue()
  print('module method callback triggered')
  user_context.actual_method_name = method_name
  user_context.actual_request_payload = json.loads(payload)

  if (user_context.actual_method_name == user_context.expected_method_name):
    if (user_context.actual_request_payload == user_context.expected_request_payload):
      print('method and payload matched. returning response')
      result.response = json.dumps(user_context.response)
      result.status = user_context.status_code
    else:
      print("request payload doesn't match")
      print("expected: " + user_context.expected_request_payload)
      print("received: " + user_context.actual_request_payload)
      result.status = 500
  else:
    print("method name doesn't match")
    print("expected: '" + user_context.expected_method_name + "'")
    print("received: '" + user_context.actual_method_name + "'")
    result.status = 404

  user_context.event.set()
  return result

class ModuleGlue:
  object_count = 1
  object_map = {}

  def _finish_connection(self, client):
    connection_id = 'moduleObject_' + str(self.object_count)
    self.object_count += 1
    self.object_map[connection_id] = client
    return ConnectResponse(connection_id)

  def connect_from_environment(self, transport_type):
    print ('connecting from environment')
    client = IoTHubModuleClient()
    IoTHubModuleClient.create_from_environment(client, transport_name_to_type(transport_type))
    return self._finish_connection(client)

  def connect(self, transport_type, connection_string, ca_certificate):
    print('connecting using ' + transport_type)
    client = IoTHubModuleClient(connection_string, transport_name_to_type(transport_type))
    if (ca_certificate.cert != None):
      client.set_option("TrustedCerts", ca_certificate.cert)
    return self._finish_connection(client)

  def disconnect(self, connection_id):
    print ('disconnecting ' + connection_id)
    if (connection_id in self.object_map):
      del self.object_map[connection_id]

  def enable_input_messages(self, connection_id):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")

  def enable_methods(self, connection_id):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")

  def enable_twin(self, connection_id):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    context = TwinCallbackContext()
    client.set_module_twin_callback(device_twin_callback, context)
    print('set module twin callback complete.  waiting')
    context.event.wait()
    context.event.clear()
    self.object_map[twin_key(connection_id)] = context

  def send_event(self, connection_id, event_body):
    print ('sending event on ' + connection_id)
    event = threading.Event()
    msg = IoTHubMessage(event_body)
    self.object_map[connection_id].send_event_async(msg, send_confirmation_callback, event)
    print('send complete.  waiting')
    event.wait()
    print('send confirmation received')

  def wait_for_input_message(self, connection_id, input_name):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    context = MessageCallbackContext()
    client.set_message_callback(input_name, receive_message_callback, context)
    print('waiting for input message')
    context.event.wait()
    print('input message received')

    #unset the callback
    #client.set_message_callback(input_name, None, None)
    return context.response

  def invoke_module_method(self, connection_id, device_id, module_id, method_invoke_parameters):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    method_name = method_invoke_parameters['methodName']
    payload = method_invoke_parameters['payload']
    timeout = method_invoke_parameters['responseTimeoutInSeconds']
    context = MethodInvokeContext()
    client.invoke_method_async(device_id, module_id, method_name, payload, timeout, method_invoke_callback, context)
    print('waiting for module method invoke response')
    context.event.wait()
    print('module method invoke response received')
    return context.payload

  def invoke_device_method(self, connection_id, device_id, method_invoke_parameters):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    method_name = method_invoke_parameters['methodName']
    payload = method_invoke_parameters['payload']
    timeout = method_invoke_parameters['responseTimeoutInSeconds']
    context = MethodInvokeContext()
    client.invoke_method_async(device_id, method_name, payload, timeout, method_invoke_callback, context)
    print('waiting for device method invoke response')
    context.event.wait()
    print('device method invoke response received')
    return context.payload

  def roundtrip_method_call(self, connection_id, methodName, requestAndResponse):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    context = MethodCallbackContext(methodName, requestAndResponse.request_payload['payload'], requestAndResponse.response_payload, requestAndResponse.status_code)
    client.set_module_method_callback(module_method_callback, context)
    print('waiting for method call')
    context.event.wait()
    print('method call received')

  def send_output_event(self, connection_id, output_name, event_body):
    print ('sending event on ' + connection_id + ',' + output_name)
    event = threading.Event()
    msg = IoTHubMessage(event_body)
    self.object_map[connection_id].send_event_async(output_name, msg, send_confirmation_callback, event)
    print('send complete.  waiting')
    event.wait()
    print('send confirmation received')

  def wait_for_desired_property_patch(self, connection_id):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    if (not twin_key(connection_id) in self.object_map):
      raise Exception("no twin context")
    context = self.object_map[twin_key(connection_id)]
    print("waiting for twin patch response")
    context.event.wait()
    context.event.clear()
    print("twin patch response received")
    return context.latest_payload

  def get_twin(self, connection_id):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    if (not twin_key(connection_id) in self.object_map):
      raise Exception("no twin context")
    context = self.object_map[twin_key(connection_id)]

    return { "properties": context.current_complete_twin }

  def send_twin_patch(self, connection_id, props):
    if (not connection_id in self.object_map):
      raise Exception("connection_id is invalid")
    client = self.object_map[connection_id]
    event = threading.Event()
    propstring = json.dumps(props)
    IoTHubModuleClient.send_reported_state(client, propstring, len(propstring), reported_state_callback, event)
    print("waiting for send reported state confirmation")
    event.wait()
    print("send reported state confirmation received")

  def cleanup_resources(self):
    listcopy  = list(self.object_map.keys())
    for key in listcopy:
      print("object {} not cleaned up".format(key))
      self.disconnect(key)
