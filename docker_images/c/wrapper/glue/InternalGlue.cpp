// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

// InternalGlue.cpp is inherited as a polymorphic class by DeviceGlue and ModuleGlue.

#include "InternalGlue.h"
#include "GlueUtils.h"
#include "json.h"

#ifndef MU_ENUM_TO_STRING
#define MU_ENUM_TO_STRING ENUM_TO_STRING
#endif


InternalGlue::InternalGlue()
{
    IoTHub_Init();
}

InternalGlue::~InternalGlue()
{
}

static void connectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS result, IOTHUB_CLIENT_CONNECTION_STATUS_REASON reason, void *user_context)
{
    (void)reason;
    (void)user_context;
    // DOES NOT TAKE INTO ACCOUNT NETWORK OUTAGES
    ::time_t timetime = ::time(nullptr);
    if (result == IOTHUB_CLIENT_CONNECTION_AUTHENTICATED)
    {
        std::cout << ::asctime(::localtime(&timetime)) << "the client (" << user_context << ") is connected to edgehub / iothub" << std::endl;
    }
    else
    {
        std::cout << ::asctime(::localtime(&timetime)) << "the client (" << user_context << ") has been disconnected" << std::endl;
    }
}

void setConnectionStatusCallback(IOTHUB_CLIENT_CORE_HANDLE client)
{
    IOTHUB_CLIENT_RESULT ret;
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    // Setting connection status callback to get indication of connection to edgehub / iothub
    ret = IoTHubClientCore_SetConnectionStatusCallback(client, connectionStatusCallback, client);
    ThrowIfFailed(ret, "IoTHubClientCore_SetConnectionStatusCallback");
}

std::string InternalGlue::Connect(const char *transportType, std::string connectionString, std::string caCertificate)
{
    // NOTE: Currently not using the caCertificate. The TLS Handshake between the module and edgeHub will fail
    // unless this cert is in the trusted certificate store.

    std::cout << "InternalGlue::Connect for " << transportType << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client;
    IOTHUB_CLIENT_TRANSPORT_PROVIDER protocol = protocolFromTransportName(transportType);
    if ((client = IoTHubClientCore_CreateFromConnectionString(connectionString.c_str(), protocol)) == NULL)
    {
        throw new std::runtime_error("failed to create client");
    }
    else
    {
        char address[32];

        sprintf(address, "%p", client);
        std::cout << "InternalGlue::Connect Client Pointer: " << address << std::endl;
        bool traceOn = true;
        bool rawTraceOn = true;
        size_t sasTokenLifetime = 3600;
        IoTHubClientCore_SetOption(client, "logtrace", &traceOn);
        IoTHubClientCore_SetOption(client, "rawlogtrace", &rawTraceOn);
        IoTHubClientCore_SetOption(client, "sas_token_lifetime", &sasTokenLifetime);
        
        std::string clientId = getNextClientId();
        this->clientMap[clientId] = (void *)client;

        setConnectionStatusCallback(client);

        std::string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
        std::cout << "returning " << ret << std::endl;
        return ret;
    }
}


void InternalGlue::Disconnect(std::string connectionId)
{
    std::cout << "InternalGlue::Disconnect for " << connectionId << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (client)
    {
        this->clientMap.erase(connectionId);
        std::cout << "Destroying client(" << (void*)client << ")" << std::endl;
        IoTHubClientCore_Destroy(client);
    }
    twin_callback_struct *twin_cb = (twin_callback_struct *)this->twinMap[connectionId];
    if (twin_cb)
    {
        this->twinMap.erase(connectionId);
        delete twin_cb;
    }
}

void InternalGlue::EnableMethods(std::string connectionId)
{
    std::cout << "InternalGlue::EnableMethods for " << connectionId << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }
}

std::string add_patch_to_twin(std::string prev_complete_twin, std::string patch)
{
    // add twin patch to complete twin 
    JSON_Value *twin_root_value;
    JSON_Value *patch_root_value;
    JSON_Object *twin_root_object;
    if ((twin_root_value = json_parse_string(prev_complete_twin.c_str())) == NULL)
    {
        throw new std::runtime_error("parson error");
    }
    else if ((patch_root_value = json_parse_string(patch.c_str())) == NULL)
    {
        throw new std::runtime_error("parson error");
    }
    else if ((twin_root_object = json_value_get_object(twin_root_value)) == NULL)
    {
        throw new std::runtime_error("parson error");
    }
    else if ((json_object_set_value(twin_root_object, "desired", patch_root_value)) != JSONSuccess)
    {
        throw new std::runtime_error("parson error");
    }

    std::string updated_twin_s = std::string(json_serialize_to_string(twin_root_value));
    json_value_free(twin_root_value); //implicitly frees twin_root_object and patch_root_value as well

    return updated_twin_s;
}

void twinCallback(DEVICE_TWIN_UPDATE_STATE update_state, const unsigned char *payLoad, const size_t size, void *userContextCallback)
{
    std::cout << "twinCallback called with state " << update_state << std::endl;
    twin_callback_struct *response = (twin_callback_struct *)userContextCallback;
    response->latest_payload = std::string(reinterpret_cast<const char *>(payLoad), size);

    if (update_state == DEVICE_TWIN_UPDATE_COMPLETE)
    {
        // the device twin update is a total twin update
        response->current_complete = std::string(reinterpret_cast<const char *>(payLoad), size);
        std::cout << "complete twin:" << response->current_complete << std::endl;
    }
    else if (update_state == DEVICE_TWIN_UPDATE_PARTIAL)
    {
        // the device twin update is a patch, so we should only patch
        response->current_complete = add_patch_to_twin(response->current_complete, response->latest_payload);
        std::cout << "latest payload:" << response->latest_payload << std::endl;
        std::cout << "complete twin: " << response->current_complete << std::endl;
        response->cvp.notify_one();
    }
    response->cv.notify_one();
}

void InternalGlue::EnableTwin(std::string connectionId)
{
    IOTHUB_CLIENT_RESULT ret;

    std::cout << "InternalGlue::EnableTwin for " << connectionId << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    twin_callback_struct *resp = new twin_callback_struct;
    ret = IoTHubClientCore_SetDeviceTwinCallback(client, twinCallback, resp);
    ThrowIfFailed(ret, "IoTHubClientCore_SetDeviceTwinCallback");

    std::cout << "waiting for initial Twin response" << std::endl;
    {
        std::unique_lock<std::mutex> lk(resp->m);
        resp->cv.wait(lk);
    }
    std::cout << "initial Twin response received" << std::endl;

    if (resp->latest_payload.empty())
    {
        throw new std::runtime_error("twin not enabled");
    }
    this->twinMap[connectionId] = (void *)resp;
}

void InternalGlue::SendEvent(std::string connectionId, std::string eventBody)
{
    std::cout << "InternalGlue::SendEvent for " << connectionId << std::endl;
    std::cout << eventBody << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    std::mutex m;
    std::condition_variable cv;

    IOTHUB_MESSAGE_HANDLE message = stringToMessage(eventBody);
    std::cout << "calling IoTHubClient_SendEventAsync" << std::endl;
    IOTHUB_CLIENT_RESULT ret = IoTHubClientCore_SendEventAsync(client, message, sendEventCallback, &cv);
    ThrowIfFailed(ret, "IoTHubClientCore_SendEventAsync");

    std::cout << "waiting for send confirmation" << std::endl;
    {
        std::unique_lock<std::mutex> lk(m);
        cv.wait(lk);
    }
    std::cout << "send confirmation received" << std::endl;
}

IOTHUBMESSAGE_DISPOSITION_RESULT receiveMessageCallback(IOTHUB_MESSAGE_HANDLE message, void *userContextCallback)
{
    std::cout << "receiveMessageCallback called" << std::endl;
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
            response->response_string = std::string("WARNING: IoTHubMessage_GetByteArray returned ") + MU_ENUM_TO_STRING(IOTHUB_MESSAGE_RESULT, ret);
            std::cout << response->response_string << std::endl;
        }
    }
    std::cout << "string == " << response->response_string << std::endl;
    response->cv.notify_one();
    return IOTHUBMESSAGE_ACCEPTED;
}

int methodCallback(const char *method_name, const unsigned char *payload, const size_t size, unsigned char **response, size_t *response_size, void *userContextCallback)
{
    std::cout << "methodCallback called" << std::endl;
    int result;

    method_callback_struct *cb_data = (method_callback_struct *)userContextCallback;
    cb_data->actual_method_name = std::string(reinterpret_cast<const char *>(method_name));
    cb_data->actual_request_payload = std::string(reinterpret_cast<const char *>(payload), size);

    if (cb_data->actual_method_name.compare(cb_data->expected_method_name) == 0)
    {
        if (cb_data->expected_request_payload.compare(cb_data->actual_request_payload) == 0)
        {
            std::cout << "method and payload matched.  returning response" << std::endl;
            *response_size = cb_data->response.length();
            *response = (unsigned char *)malloc(*response_size);
            if (response == NULL)
            {
                throw new std::runtime_error("failed to allocate memory for response");
            };
            (void)memcpy(*response, cb_data->response.c_str(), *response_size);
            result = cb_data->status_code;
        }
        else
        {
            std::cout << "request payload doesn't match" << std::endl;
            std::cout << "expected: " << cb_data->expected_request_payload << std::endl;
            std::cout << "received: " << cb_data->actual_request_payload << std::endl;
            result = 500;
        }
    }
    else
    {
        std::cout << "method name doesn't match" << std::endl;
        std::cout << "expected: " << cb_data->expected_method_name << std::endl;
        std::cout << "received: " << cb_data->actual_method_name << std::endl;
        result = 404;
    }

    cb_data->cv.notify_one();
    return result;
}

void InternalGlue::WaitForMethodAndReturnResponse(std::string connectionId, std::string methodName, std::string requestAndResponse)
{
    IOTHUB_CLIENT_RESULT ret;

    std::cout << "InternalGlue::WaitForMethodAndReturnResponse for " << connectionId << " and " << methodName << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    std::string expectedRequest, response;
    int statusCode;
    parseMethodRequestAndResponse(requestAndResponse, &expectedRequest, &response, &statusCode);

    method_callback_struct cb_data;
    cb_data.expected_method_name = methodName;
    cb_data.expected_request_payload = expectedRequest;
    cb_data.response = response;
    cb_data.status_code = statusCode;
    ret = IoTHubClientCore_SetDeviceMethodCallback(client, methodCallback, &cb_data);
    ThrowIfFailed(ret, "IoTHubClientCore_SetDeviceMethodCallback");

    std::cout << "waiting for method call" << std::endl;
    {
        std::unique_lock<std::mutex> lk(cb_data.m);
        cb_data.cv.wait(lk);
    }
    std::cout << "method call received" << std::endl;
}


std::string InternalGlue::WaitForDesiredPropertyPatch(std::string connectionId)
{
    std::cout << "InternalGlue::WaitForDesiredPropertyPatch for " << connectionId << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    twin_callback_struct *resp = (twin_callback_struct *)(this->twinMap[connectionId]);
    if (!resp)
    {
        throw new std::runtime_error("no twin callback struct");
    }

    std::cout << "waiting for Twin patch response" << std::endl;
    {
        std::unique_lock<std::mutex> lk(resp->m);
        resp->cv.wait(lk);
    }
    std::cout << "Twin patch response received" << std::endl;

    return addJsonWrapperObject(resp->latest_payload, "desired");
}

std::string InternalGlue::GetTwin(std::string connectionId)
{
    std::cout << "InternalGlue::GetTwin for " << connectionId << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    twin_callback_struct *resp = (twin_callback_struct *)(this->twinMap[connectionId]);
    if (!resp)
    {
        throw new std::runtime_error("no twin callback struct");
    }

    return resp->current_complete;
}

void reportedStateCallback(int status_code, void *userContextCallback)
{
    std::cout << "reportedStateCallback called with " << status_code << std::endl;
    std::condition_variable *cv = (std::condition_variable *)userContextCallback;
    cv->notify_one();
}

void InternalGlue::SendTwinPatch(std::string connectionId, std::string props)
{
    std::cout << "InternalGlue::SendTwinPatch for " << connectionId << std::endl;
    std::cout << props << std::endl;
    IOTHUB_CLIENT_CORE_HANDLE client = (IOTHUB_CLIENT_CORE_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    std::mutex m;
    std::condition_variable cv;
    std::string reported = Json(props).getSubObject("reported");

    IOTHUB_CLIENT_RESULT res = IoTHubClientCore_SendReportedState(client, (const unsigned char *)reported.c_str(), reported.length(), reportedStateCallback, &cv);
    ThrowIfFailed(res, "IoTHubClientCore_SendReportedState");

    std::cout << "waiting for send reported state confirmation" << std::endl;
    {
        std::unique_lock<std::mutex> lk(m);
        cv.wait(lk);
    }
    std::cout << "send reported state confirmation received" << std::endl;
}

void InternalGlue::CleanupResources()
{
    std::cout << "InternalGlue::CleanupResources called" << std::endl;
    // copy the map since we're removing things from it while we're iterating over it.
    std::map<std::string, void *> mapCopy = this->clientMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        std::cout << "missed cleanup of " << iter->first << std::endl;
        this->Disconnect(iter->first);
    }
}
