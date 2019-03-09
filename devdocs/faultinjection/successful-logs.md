
test_connect_disconnect_fi.py
```
{"message": "PYTEST: HORTON: starting run: ['--timeout', '90', '-vv', '--showlocals', '--tb=short', '--scenario=edgehub_module_fi', '--c-wrapper', 'test_connect_disconnect_fi.py']"}
{"message": "PYTEST: HORTON: Preforming pre-session cleanup"}
{"message": "PYTEST: HORTON: pre-session cleanup complete"}
{"message": "PYTEST: HORTON: Entering module test_connect_disconnect_fi"}
{"message": "PYTEST: HORTON: Entering function test_module_client_connect_enable_twin_disconnect_fi"}
{"message": "PYTEST: Connect Test Module Client"}
{"message": "PYTEST: Callng 'ModuleApi.connect_from_environment'(<adapters.rest.rest_module_api.ModuleApi object at 0x7efe66828390>, 'mqtt')"}
InternalGlue::ConnectFromEnvironment for mqtt
returning { "connectionId" : "moduleClient_1"}
{"message": "PYTEST: 'ModuleApi.connect_from_environment' returned None"}
{"message": "PYTEST: Enable Twin on Module Client"}
{"message": "PYTEST: Callng 'ModuleApi.enable_twin'(<adapters.rest.rest_module_api.ModuleApi object at 0x7efe66828390>)"}
InternalGlue::EnableTwin for moduleClient_1
waiting for initial Twin response
-> 01:38:03 CONNECT | VER: 4 | KEEPALIVE: 240 | FLAGS: 192 | USERNAME: yosephhub.azure-devices.net/yoseph-E2E-Virtual-Machine_yoseph_88402478/cMod/?api-version=2017-11-08-preview&DeviceClientType=iothubclient%2f1.2.14%20(native%3b%20Linux%3b%20x86_64) | PWD: XXXX | CLEAN: 0
<- 01:38:04 CONNACK | SESSION_PRESENT: false | RETURN_CODE: 0x0
Sat Mar  9 01:38:04 2019
the module client is connected to edgehub / iothub
-> 01:38:04 SUBSCRIBE | PACKET_ID: 2 | TOPIC_NAME: $iothub/twin/res/# | QOS: 0
<- 01:38:04 SUBACK | PACKET_ID: 2 | RETURN_CODE: 0
-> 01:38:04 PUBLISH | IS_DUP: false | RETAIN: 0 | QOS: DELIVER_AT_MOST_ONCE | TOPIC_NAME: $iothub/twin/GET/?$rid=3
<- 01:38:04 PUBLISH | IS_DUP: false | RETAIN: 0 | QOS: DELIVER_AT_MOST_ONCE = 0x00 | TOPIC_NAME: $iothub/twin/res/200/?$rid=3 | PAYLOAD_LEN: 52
twinCallback called with state 0
initial Twin response received
{"message": "PYTEST: 'ModuleApi.enable_twin' returned None"}
-> 01:38:04 SUBSCRIBE | PACKET_ID: 4 | TOPIC_NAME: $iothub/twin/PATCH/properties/desired/# | QOS: 0
{"message": "PYTEST: disconnecting edgehub from network"}
<- 01:38:04 SUBACK | PACKET_ID: 4 | RETURN_CODE: 0
{"message": "PYTEST: connecting edgehub to network"}
{"message": "PYTEST:  edgeHub = client.containers.get(EDGEHUB_NAME)"}
{"message": "PYTEST: edge_network.connect(EDGEHUB_NAME)"}
{"message": "PYTEST: Disconnect Module Client"}
{"message": "PYTEST: Callng 'ModuleApi.disconnect'(<adapters.rest.rest_module_api.ModuleApi object at 0x7efe66828390>)"}
InternalGlue::Disconnect for moduleClient_1
```
