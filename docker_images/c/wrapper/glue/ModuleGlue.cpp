// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include "ModuleGlue.h"
#include "GlueUtils.h"

static int clientCount = 0;
static std::string client_prefix = "moduleClient_";

ModuleGlue::ModuleGlue()
{
    IoTHub_Init();
}

ModuleGlue::~ModuleGlue()
{
}

std::string ModuleGlue::getNextClientId()
{
    static int clientCount = 0;
    static std::string client_prefix = "moduleClient_";
    return client_prefix + std::to_string(++clientCount);
}


std::string ModuleGlue::ConnectFromEnvironment(const char *transportType)
{
    std::cout << "ModuleGlue::ConnectFromEnvironment for " << transportType << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client;
    IOTHUB_CLIENT_TRANSPORT_PROVIDER protocol = protocolFromTransportName(transportType);
    if ((client = IoTHubModuleClient_CreateFromEnvironment(protocol)) == NULL)
    {
        throw new std::runtime_error("failed to create client");
    }
    else
    {
        bool traceOn = true;
        bool rawTraceOn = true;
        size_t sasTokenLifetime = 3600;
        IoTHubModuleClient_SetOption(client, "logtrace", &traceOn);
        IoTHubModuleClient_SetOption(client, "rawlogtrace", &rawTraceOn);
        IoTHubModuleClient_SetOption(client, "sas_token_lifetime", &sasTokenLifetime);
        std::cout << "Module client(" << (void*)client << ") created" << std::endl;
        

        std::string clientId = getNextClientId();
        this->clientMap[clientId] = (void *)client;

        setConnectionStatusCallback(client);

        std::string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
        std::cout << "returning " << ret << std::endl;
        return ret;
    }
}

void ModuleGlue::EnableInputMessages(std::string connectionId)
{
    std::cout << "ModuleGlue::EnableInputMessages for " << connectionId << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }
}

void ModuleGlue::SendOutputEvent(std::string connectionId, std::string outputName, std::string eventBody)
{
    std::cout << "ModuleGlue::SendOutputEvent for " << connectionId << " and " << outputName << std::endl;
    std::cout << eventBody << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    std::mutex m;
    std::condition_variable cv;

    IOTHUB_MESSAGE_HANDLE message = stringToMessage(eventBody);

    std::cout << "calling IoTHubClient_SendEventAsync" << std::endl;
    IOTHUB_CLIENT_RESULT ret = IoTHubModuleClient_SendEventToOutputAsync(client, message, outputName.c_str(), sendEventCallback, &cv);
    ThrowIfFailed(ret, "IoTHubModuleClient_SendEventToOutputAsync");

    std::cout << "waiting for send confirmation" << std::endl;
    {
        std::unique_lock<std::mutex> lk(m);
        cv.wait(lk);
    }
    std::cout << "send confirmation received" << std::endl;
}

std::string ModuleGlue::WaitForInputMessage(std::string connectionId, std::string inputName)
{
    IOTHUB_CLIENT_RESULT ret;

    std::cout << "ModuleGlue::WaitForInputMessage for " << connectionId << " and " << inputName << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    message_response_struct resp;
    ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), receiveMessageCallback, &resp);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback");

    std::cout << "waiting for input message" << std::endl;
    try
    {
        std::unique_lock<std::mutex> lk(resp.m);
        resp.cv.wait(lk);
    }
    catch (...)
    {
        ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), NULL, NULL);
        ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback(NULL)");
        throw;
    }

    std::cout << "input message received" << std::endl;
    ret = IoTHubModuleClient_SetInputMessageCallback(client, inputName.c_str(), NULL, NULL);
    ThrowIfFailed(ret, "IoTHubModuleClient_SetInputMessageCallback(NULL)");

    return addJsonWrapperObject(resp.response_string, "body");
}

void method_invoke_callback(IOTHUB_CLIENT_RESULT result, int responseStatus, unsigned char *responsePayload, size_t responsePayloadSize, void *context)
{
    (void)result;
    (void)responseStatus;
    method_invoke_response *resp = (method_invoke_response *)context;
    resp->statusCode = responseStatus;
    resp->payload = std::string(reinterpret_cast<const char *>(responsePayload), responsePayloadSize);

    resp->cv.notify_one();
}

std::string ModuleGlue::InvokeModuleMethod(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters)
{
    std::cout << "ModuleGlue::InvokeModuleMethod for " << connectionId << " and " << deviceId << " and " << moduleId << std::endl;
    std::cout << methodInvokeParameters << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    method_invoke_response response;
    std::string methodName;
    std::string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);
    IoTHubModuleClient_ModuleMethodInvokeAsync(client, deviceId.c_str(), moduleId.c_str(), methodName.c_str(), payload.c_str(), timeout, method_invoke_callback, &response);

    std::cout << "waiting for module method invoke response" << std::endl;
    {
        std::unique_lock<std::mutex> lk(response.m);
        response.cv.wait(lk);
    }
    std::cout << "module method invoke response received" << std::endl;
    return makeInvokeResponse(response.statusCode, response.payload);
}

std::string ModuleGlue::InvokeDeviceMethod(std::string connectionId, std::string deviceId, std::string methodInvokeParameters)
{
    std::cout << "ModuleGlue::InvokeDeviceMethod for " << connectionId << " and " << deviceId << std::endl;
    std::cout << methodInvokeParameters << std::endl;
    IOTHUB_MODULE_CLIENT_HANDLE client = (IOTHUB_MODULE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    method_invoke_response response;
    std::string methodName;
    std::string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);
    IoTHubModuleClient_DeviceMethodInvokeAsync(client, deviceId.c_str(), methodName.c_str(), payload.c_str(), timeout, method_invoke_callback, &response);

    std::cout << "waiting for device method invoke response" << std::endl;
    {
        std::unique_lock<std::mutex> lk(response.m);

        response.cv.wait(lk);
    }
    std::cout << "device method invoke response received" << std::endl;

    return makeInvokeResponse(response.statusCode, response.payload);
}

