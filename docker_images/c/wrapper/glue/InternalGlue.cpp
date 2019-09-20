// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

// InternalGlue.cpp is inherited as a polymorphic class by DeviceGlue and ModuleGlue.

#include <string>
#include <mutex>
#include <iostream>
#include <condition_variable>

#define USE_EDGE_MODULES
#define USE_PROV_MODULE
#include "internal/iothub_client_edge.h"
#include "iothub_module_client.h"
#include "iothub_client_options.h"
#include "iothubtransportamqp.h"
#include "iothubtransportamqp_websockets.h"
#include "iothubtransportmqtt.h"
#include "iothubtransportmqtt_websockets.h"
#include "iothub.h"
#include "parson.h"

#include "GlueUtils.h"
#include "InternalGlue.h"

using namespace std;

#ifndef MU_ENUM_TO_STRING
#define MU_ENUM_TO_STRING ENUM_TO_STRING
#endif

struct twin_callback_struct
{
    condition_variable cv;
    mutex m;
    condition_variable cvp;
    mutex mp;
    string latest_payload;
    string current_complete;
};

struct message_response_struct
{
    mutex m;
    condition_variable cv;
    string response_string;
};

struct method_callback_struct
{
    mutex m;
    condition_variable cv;
    string expected_method_name;
    string expected_request_payload;
    string actual_method_name;
    string actual_request_payload;
    string response;
    int status_code;
};

struct method_invoke_response
{
    mutex m;
    condition_variable cv;
    int statusCode;
    string payload;
};

void ThrowIfFailed(IOTHUB_CLIENT_RESULT ret, string functionName)
{
    if (ret != IOTHUB_CLIENT_OK)
    {
        throw new runtime_error(functionName + " returned " + MU_ENUM_TO_STRING(IOTHUB_CLIENT_RESULT, ret));
    }
}

IOTHUB_CLIENT_TRANSPORT_PROVIDER protocolFromTransportName(const char *transportType)
{
    if (strcmp(transportType, "mqtt") == 0)
    {
        return MQTT_Protocol;
    }
    else if (strcmp(transportType, "mqttws") == 0)
    {
        return MQTT_WebSocket_Protocol;
    }
    else if (strcmp(transportType, "amqp") == 0)
    {
        return AMQP_Protocol;
    }
    else if (strcmp(transportType, "amqpws") == 0)
    {
        return AMQP_Protocol_over_WebSocketsTls;
    }
    else
    {
        string transport_string = "Unknown transport: ";
        throw new runtime_error(transport_string + transportType);
    }
}

InternalGlue::InternalGlue()
{
    IoTHub_Init();
}

InternalGlue::~InternalGlue()
{
}

void setConnectionStatusCallback(IOTHUB_MODULE_CLIENT_HANDLE);
static void connectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS, IOTHUB_CLIENT_CONNECTION_STATUS_REASON, void *);

string InternalGlue::Connect(const char *transportType, std::string connectionString, std::string caCertificate)
{
    // NOTE: Currently not using the caCertificate. The TLS Handshake between the module and edgeHub will fail
    // unless this cert is in the trusted certificate store.

    cout << "InternalGlue::Connect for " << transportType << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client;
    IOTHUB_CLIENT_TRANSPORT_PROVIDER protocol = protocolFromTransportName(transportType);
    if ((client = IoTHubModuleClient_CreateFromConnectionString(connectionString.c_str(), protocol)) == NULL)
    {
        throw new runtime_error("failed to create client");
    }
    else
    {
        char address[32];

        sprintf(address, "%p", client);
        cout << "InternalGlue::Connect Client Pointer: " << address << endl;
        bool traceOn = true;
        bool rawTraceOn = true;
        size_t sasTokenLifetime = 3600;
        IoTHubModuleClient_SetOption(client, "logtrace", &traceOn);
        IoTHubModuleClient_SetOption(client, "rawlogtrace", &rawTraceOn);
        IoTHubModuleClient_SetOption(client, "sas_token_lifetime", &sasTokenLifetime);
        
        string clientId = getNextClientId();
        this->clientMap[clientId] = (void *)client;

        setConnectionStatusCallback(client);

        string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
        cout << "returning " << ret << endl;
        return ret;
    }
}

string InternalGlue::ConnectFromEnvironment(const char *transportType)
{
    cout << "InternalGlue::ConnectFromEnvironment for " << transportType << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client;
    IOTHUB_CLIENT_TRANSPORT_PROVIDER protocol = protocolFromTransportName(transportType);
    if ((client = IoTHubModuleClient_CreateFromEnvironment(protocol)) == NULL)
    {
        throw new runtime_error("failed to create client");
    }
    else
    {
        bool traceOn = true;
        bool rawTraceOn = true;
        size_t sasTokenLifetime = 3600;
        IoTHubModuleClient_SetOption(client, "logtrace", &traceOn);
        IoTHubModuleClient_SetOption(client, "rawlogtrace", &rawTraceOn);
        IoTHubModuleClient_SetOption(client, "sas_token_lifetime", &sasTokenLifetime);
        cout << "Module client(" << (void*)client << ") created" << endl;
        

        string clientId = getNextClientId();
        this->clientMap[clientId] = (void *)client;

        setConnectionStatusCallback(client);

        string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
        cout << "returning " << ret << endl;
        return ret;
    }
}

void InternalGlue::Disconnect(string connectionId)
{
    cout << "InternalGlue::Disconnect for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (client)
    {
        this->clientMap.erase(connectionId);
        cout << "Destroying module client(" << (void*)client << ")" << endl;
        IoTHubModuleClient_Destroy(client);
    }
    twin_callback_struct *twin_cb = (twin_callback_struct *)this->twinMap[connectionId];
    if (twin_cb)
    {
        this->twinMap.erase(connectionId);
        delete twin_cb;
    }
}

void InternalGlue::EnableInputMessages(string connectionId)
{
    cout << "InternalGlue::EnableInputMessages for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }
}

void InternalGlue::EnableMethods(string connectionId)
{
    cout << "InternalGlue::EnableMethods for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }
}

string add_patch_to_twin(string prev_complete_twin, string patch)
{
    // add twin patch to complete twin 
    JSON_Value *twin_root_value;
    JSON_Value *patch_root_value;
    JSON_Object *twin_root_object;
    if ((twin_root_value = json_parse_string(prev_complete_twin.c_str())) == NULL)
    {
        throw new runtime_error("parson error");
    }
    else if ((patch_root_value = json_parse_string(patch.c_str())) == NULL)
    {
        throw new runtime_error("parson error");
    }
    else if ((twin_root_object = json_value_get_object(twin_root_value)) == NULL)
    {
        throw new runtime_error("parson error");
    }
    else if ((json_object_set_value(twin_root_object, "desired", patch_root_value)) != JSONSuccess)
    {
        throw new runtime_error("parson error");
    }

    string updated_twin_s = string(json_serialize_to_string(twin_root_value));
    json_value_free(twin_root_value); //implicitly frees twin_root_object and patch_root_value as well

    return updated_twin_s;
}

void twinCallback(DEVICE_TWIN_UPDATE_STATE update_state, const unsigned char *payLoad, const size_t size, void *userContextCallback)
{
    cout << "twinCallback called with state " << update_state << endl;
    twin_callback_struct *response = (twin_callback_struct *)userContextCallback;
    response->latest_payload = string(reinterpret_cast<const char *>(payLoad), size);

    if (update_state == DEVICE_TWIN_UPDATE_COMPLETE)
    {
        // the device twin update is a total twin update
        response->current_complete = string(reinterpret_cast<const char *>(payLoad), size);
    }
    else if (update_state == DEVICE_TWIN_UPDATE_PARTIAL)
    {
        // the device twin update is a patch, so we should only patch
        response->current_complete = add_patch_to_twin(response->current_complete, response->latest_payload);
        response->cvp.notify_one();
    }
    response->cv.notify_one();
}

void InternalGlue::EnableTwin(string connectionId)
{
    IOTHUB_CLIENT_RESULT ret;

    cout << "InternalGlue::EnableTwin for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    twin_callback_struct *resp = new twin_callback_struct;
    ret = IoTHubModuleClient_SetModuleTwinCallback(client, twinCallback, resp);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetModuleTwinCallback");

    cout << "waiting for initial Twin response" << endl;
    {
        unique_lock<mutex> lk(resp->m);
        resp->cv.wait(lk);
    }
    cout << "initial Twin response received" << endl;

    if (resp->latest_payload.empty())
    {
        throw new runtime_error("twin not enabled");
    }
    this->twinMap[connectionId] = (void *)resp;
}

void sendEventCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void *userContextCallback)
{
    cout << "sendEventCallback called with " << MU_ENUM_TO_STRING(IOTHUB_CLIENT_CONFIRMATION_RESULT, result) << endl;
    condition_variable *cv = (condition_variable *)userContextCallback;
    cv->notify_one();
}

void InternalGlue::SendEvent(string connectionId, string eventBody)
{
    cout << "InternalGlue::SendEvent for " << connectionId << endl;
    cout << eventBody << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    mutex m;
    condition_variable cv;

    IOTHUB_MESSAGE_HANDLE message = IoTHubMessage_CreateFromString(eventBody.c_str());
    cout << "calling IoTHubClient_SendEventAsync" << endl;
    IOTHUB_CLIENT_RESULT ret = IoTHubModuleClient_SendEventAsync(client, message, sendEventCallback, &cv);
    ThrowIfFailed(ret, "IoTHubModuleClient_SendEventAsync");

    cout << "waiting for send confirmation" << endl;
    {
        unique_lock<mutex> lk(m);
        cv.wait(lk);
    }
    cout << "send confirmation received" << endl;
}

void InternalGlue::SendOutputEvent(string connectionId, string outputName, string eventBody)
{
    cout << "InternalGlue::SendOutputEvent for " << connectionId << " and " << outputName << endl;
    cout << eventBody << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    mutex m;
    condition_variable cv;

    IOTHUB_MESSAGE_HANDLE message = IoTHubMessage_CreateFromString(eventBody.c_str());
    cout << "calling IoTHubClient_SendEventAsync" << endl;
    IOTHUB_CLIENT_RESULT ret = IoTHubModuleClient_SendEventToOutputAsync(client, message, outputName.c_str(), sendEventCallback, &cv);
    ThrowIfFailed(ret, "IoTHubModuleClient_SendEventToOutputAsync");

    cout << "waiting for send confirmation" << endl;
    {
        unique_lock<mutex> lk(m);
        cv.wait(lk);
    }
    cout << "send confirmation received";
}

IOTHUBMESSAGE_DISPOSITION_RESULT receiveMessageCallback(IOTHUB_MESSAGE_HANDLE message, void *userContextCallback)
{
    cout << "receiveMessageCallback called" << endl;
    message_response_struct *response = (message_response_struct *)userContextCallback;
    const char *str = IoTHubMessage_GetString(message);
    if (str)
    {
        response->response_string = str;
    }
    else
    {
        const unsigned char *buffer;
        size_t size;
        IOTHUB_MESSAGE_RESULT ret = IoTHubMessage_GetByteArray(message, &buffer, &size);
        if (ret == IOTHUB_MESSAGE_OK)
        {
            response->response_string.assign((const char *)buffer, size);
        }
        else
        {
            response->response_string = string("WARNING: IoTHubMessage_GetByteArray returned ") + MU_ENUM_TO_STRING(IOTHUB_MESSAGE_RESULT, ret);
            cout << response->response_string << endl;
        }
    }
    cout << "string == " << response->response_string << endl;
    response->cv.notify_one();
    return IOTHUBMESSAGE_ACCEPTED;
}

string InternalGlue::WaitForInputMessage(string connectionId, string inputName)
{
    IOTHUB_CLIENT_RESULT ret;

    cout << "InternalGlue::WaitForInputMessage for " << connectionId << " and " << inputName << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    message_response_struct resp;
    ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), receiveMessageCallback, &resp);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback");

    cout << "waiting for input message" << endl;
    try
    {
        unique_lock<mutex> lk(resp.m);
        resp.cv.wait(lk);
    }
    catch (...)
    {
        ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), NULL, NULL);
        ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback(NULL)");
        throw;
    }

    cout << "input message received" << endl;
    ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), NULL, NULL);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback(NULL)");

    return resp.response_string;
}

int moduleMethodCallback(const char *method_name, const unsigned char *payload, const size_t size, unsigned char **response, size_t *response_size, void *userContextCallback)
{
    cout << "moduleMethodCallback called" << endl;
    int result;

    method_callback_struct *cb_data = (method_callback_struct *)userContextCallback;
    cb_data->actual_method_name = string(reinterpret_cast<const char *>(method_name));
    cb_data->actual_request_payload = string(reinterpret_cast<const char *>(payload), size);

    if (cb_data->actual_method_name.compare(cb_data->expected_method_name) == 0)
    {
        if (cb_data->expected_request_payload.compare(cb_data->actual_request_payload) == 0)
        {
            cout << "method and payload matched.  returning response" << endl;
            *response_size = cb_data->response.length();
            *response = (unsigned char *)malloc(*response_size);
            if (response == NULL)
            {
                throw new runtime_error("failed to allocate memory for response");
            };
            (void)memcpy(*response, cb_data->response.c_str(), *response_size);
            result = cb_data->status_code;
        }
        else
        {
            cout << "request payload doesn't match" << endl;
            cout << "expected: " << cb_data->expected_request_payload << endl;
            cout << "received: " << cb_data->actual_request_payload << endl;
            result = 500;
        }
    }
    else
    {
        cout << "method name doesn't match" << endl;
        cout << "expected: " << cb_data->expected_method_name << endl;
        cout << "received: " << cb_data->actual_method_name << endl;
        result = 404;
    }

    cb_data->cv.notify_one();
    return result;
}

void parseMethodRequestAndResponse(string requestAndResponse, string *expectedRequest, string *response, int *statusCode)
{
    JSON_Value *root_value;
    JSON_Object *root_object;
    if ((root_value = json_parse_string(requestAndResponse.c_str())) == NULL)
    {
        throw new runtime_error("parson error");
    }
    else if ((root_object = json_value_get_object(root_value)) == NULL)
    {
        throw new runtime_error("parson error");
    }
    *expectedRequest = getJsonObjectAsString(root_object, "requestPayload.payload");
    *response = getJsonObjectAsString(root_object, "responsePayload");
    *statusCode = (int)json_object_get_number(root_object, "statusCode");
    json_value_free(root_value); //implicitly frees root_object as well
}

void InternalGlue::RoundTripMethodCall(string connectionId, string methodName, string requestAndResponse)
{
    IOTHUB_CLIENT_RESULT ret;

    cout << "InternalGlue::RoundTripMethodCall for " << connectionId << " and " << methodName << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    string expectedRequest, response;
    int statusCode;
    parseMethodRequestAndResponse(requestAndResponse, &expectedRequest, &response, &statusCode);

    method_callback_struct cb_data;
    cb_data.expected_method_name = methodName;
    cb_data.expected_request_payload = expectedRequest;
    cb_data.response = response;
    cb_data.status_code = statusCode;
    ret = IoTHubModuleClient_SetModuleMethodCallback(client, moduleMethodCallback, &cb_data);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetModuleMethodCallback");

    cout << "waiting for method call" << endl;
    {
        unique_lock<mutex> lk(cb_data.m);
        cb_data.cv.wait(lk);
    }
    cout << "method call received" << endl;
}

static void connectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result, IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason, void *user_context)
{
    (void)reason;
    (void)user_context;
    // DOES NOT TAKE INTO ACCOUNT NETWORK OUTAGES
    std::time_t timetime = std::time(nullptr);
    if (result == IOTHUB_CLIENT_CONNECTION_AUTHENTICATED)
    {
        cout << std::asctime(std::localtime(&timetime)) << "the module client (" << user_context << ") is connected to edgehub / iothub" << endl;
    }
    else
    {
        cout << std::asctime(std::localtime(&timetime)) << "the module client (" << user_context << ") has been disconnected" << endl;
    }
}

void setConnectionStatusCallback(IOTHUB_MODULE_CLIENT_HANDLE client)
{
    IOTHUB_CLIENT_RESULT ret;
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    // Setting connection status callback to get indication of connection to edgehub / iothub
    ret = IoTHubModuleClient_SetConnectionStatusCallback(client, connectionStatusCallback, client);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetConnectionStatusCallback");
}

void method_invoke_callback(IOTHUB_CLIENT_RESULT result, int responseStatus, unsigned char *responsePayload, size_t responsePayloadSize, void *context)
{
    (void)result;
    (void)responseStatus;
    method_invoke_response *resp = (method_invoke_response *)context;
    resp->statusCode = responseStatus;
    resp->payload = string(reinterpret_cast<const char *>(responsePayload), responsePayloadSize);

    resp->cv.notify_one();
}

string InternalGlue::InvokeModuleMethod(string connectionId, string deviceId, string moduleId, string methodInvokeParameters)
{
    cout << "InternalGlue::InvokeModuleMethod for " << connectionId << " and " << deviceId << " and " << moduleId << endl;
    cout << methodInvokeParameters << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    method_invoke_response response;
    string methodName;
    string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);
    IoTHubModuleClient_ModuleMethodInvokeAsync(client, deviceId.c_str(), moduleId.c_str(), methodName.c_str(), payload.c_str(), timeout, method_invoke_callback, &response);

    cout << "waiting for module method invoke response" << endl;
    {
        unique_lock<mutex> lk(response.m);
        response.cv.wait(lk);
    }
    cout << "module method invoke response received" << endl;
    return makeInvokeResponse(response.statusCode, response.payload);
}

string InternalGlue::InvokeDeviceMethod(string connectionId, string deviceId, string methodInvokeParameters)
{
    cout << "InternalGlue::InvokeDeviceMethod for " << connectionId << " and " << deviceId << endl;
    cout << methodInvokeParameters << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    method_invoke_response response;
    string methodName;
    string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);
    IoTHubModuleClient_DeviceMethodInvokeAsync(client, deviceId.c_str(), methodName.c_str(), payload.c_str(), timeout, method_invoke_callback, &response);

    cout << "waiting for device method invoke response" << endl;
    {
        unique_lock<mutex> lk(response.m);
        response.cv.wait(lk);
    }
    cout << "device method invoke response received" << endl;

    return makeInvokeResponse(response.statusCode, response.payload);
}

string InternalGlue::WaitForDesiredPropertyPatch(string connectionId)
{
    cout << "InternalGlue::WaitForDesiredPropertyPatch for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    twin_callback_struct *resp = (twin_callback_struct *)(this->twinMap[connectionId]);
    if (!resp)
    {
        throw new runtime_error("no twin callback struct");
    }

    cout << "waiting for Twin patch response" << endl;
    {
        unique_lock<mutex> lk(resp->m);
        resp->cv.wait(lk);
    }
    cout << "Twin patch response received" << endl;

    return resp->latest_payload;
}

string InternalGlue::GetTwin(string connectionId)
{
    cout << "InternalGlue::GetTwin for " << connectionId << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    twin_callback_struct *resp = (twin_callback_struct *)(this->twinMap[connectionId]);
    if (!resp)
    {
        throw new runtime_error("no twin callback struct");
    }

    /* The C SDK's version of get (for now) doesn't actually give the full twin, just the properties.
    Here we wrap those properties within a twin structure*/
    string full_twin = "{ \"properties\": " + resp->current_complete + "}";

    return full_twin;
}

void reportedStateCallback(int status_code, void *userContextCallback)
{
    cout << "reportedStateCallback called with " << status_code << endl;
    condition_variable *cv = (condition_variable *)userContextCallback;
    cv->notify_one();
}

void InternalGlue::SendTwinPatch(string connectionId, string props)
{
    cout << "InternalGlue::SendTwinPatch for " << connectionId << endl;
    cout << props << endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }

    mutex m;
    condition_variable cv;
    const unsigned char *reportedState = (const unsigned char *)props.c_str();
    size_t reportedStateSize = props.length();

    IOTHUB_CLIENT_RESULT res = IoTHubModuleClient_SendReportedState(client, reportedState, reportedStateSize, reportedStateCallback, &cv);
    ThrowIfFailed(res, "IoTHubModuleClient_SendReportedState");

    cout << "waiting for send reported state confirmation" << endl;
    {
        unique_lock<mutex> lk(m);
        cv.wait(lk);
    }
    cout << "send reported state confirmation received" << endl;
}

void InternalGlue::CleanupResources()
{
    cout << "InternalGlue::CleanupResources called" << endl;
    // copy the map since we're removing things from it while we're iterating over it.
    map<string, void *> mapCopy = this->clientMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        cout << "missed cleanup of " << iter->first << endl;
        this->Disconnect(iter->first);
    }
}
