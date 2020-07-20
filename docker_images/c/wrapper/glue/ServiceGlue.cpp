// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <iostream>
#include <mutex>
#include <condition_variable>
#include "ServiceGlue.h"
#include "GlueUtils.h"

static int clientCount = 0;
static std::string client_prefix = "serviceClient_";

ServiceGlue::ServiceGlue()
{
}

ServiceGlue::~ServiceGlue()
{
}

void messagingOpenCallback(void *context)
{
    std::cout << "messagingOpenCallback called" << std::endl;
}

std::string ServiceGlue::Connect(std::string connectionString)
{
    std::cout << "ServiceGlue::Connect called" << std::endl;
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = NULL;
    IOTHUB_MESSAGING_CLIENT_HANDLE messaging_client = NULL;

    try
    {
        if ((client = IoTHubServiceClientAuth_CreateFromConnectionString(connectionString.c_str())) == NULL)
        {
            throw new std::runtime_error("failed to create client");
        }

        if ((messaging_client = IoTHubMessaging_Create(client)) == NULL)
        {
            throw new std::runtime_error("failed to create client");
        }

        IOTHUB_MESSAGING_RESULT ret = IoTHubMessaging_Open(messaging_client, messagingOpenCallback, NULL);
        ThrowIfFailed(ret, "IoTHubMessaging_Open");

        std::cout << "messaging client is open" << std::endl;

    }
    catch(...)
    {
        std::cout << "exception raised in ServiceGlue::Connect" << std::endl;
        if (messaging_client)
        {
            IoTHubMessaging_Destroy(messaging_client);
        }
        if (client)
        {
            IoTHubServiceClientAuth_Destroy(client);
        }
        throw;
    }

    std::string clientId = client_prefix + std::to_string(++clientCount);
    std::string ret = "{ \"connectionId\" : \"" + clientId + "\"}";

    this->clientMap[clientId] = (void*)client;
    this->messagingMap[clientId] = (void*)messaging_client;

    std::cout << "returning " << ret << std::endl;
    return ret;
}

void ServiceGlue::Disconnect(std::string connectionId)
{
    std::cout << "ServiceGlue::Disconnect for " << connectionId << std::endl;
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = (IOTHUB_SERVICE_CLIENT_AUTH_HANDLE)this->clientMap[connectionId];
    IOTHUB_MESSAGING_CLIENT_HANDLE messaging_client = (IOTHUB_MESSAGING_CLIENT_HANDLE)this->messagingMap[connectionId];

    if (messaging_client)
    {
        this->messagingMap.erase(connectionId);
        std::cout << "calling IoTHubMessaging_Close" << std::endl;
        IoTHubMessaging_Close(messaging_client);
        std::cout << "done calling IoTHubMessaging_Close" << std::endl;
        std::cout << "calling IoTHubMessaging_Destroy" << std::endl;
        IoTHubMessaging_Destroy(messaging_client);
        std::cout << "done calling IoTHubMessaging_Destroy" << std::endl;
    }
    else
    {
        std::cout << "messaging client already closed.  nothing to do." << std::endl;
    }

    if (client)
    {
        this->clientMap.erase(connectionId);
        std::cout << "calling IoTHubServiceClientAuth_Destroy" << std::endl;
        IoTHubServiceClientAuth_Destroy(client);
        std::cout << "done calling IoTHubServiceClientAuth_Destroy" << std::endl;
    }
    else
    {
        std::cout << "client already closed.  nothing to do." << std::endl;
    }
}

std::string ServiceGlue::_invokeMethodCommon(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters)
{
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = (IOTHUB_SERVICE_CLIENT_AUTH_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }
    IOTHUB_SERVICE_CLIENT_DEVICE_METHOD_HANDLE serviceClientDeviceMethodHandle = IoTHubDeviceMethod_Create(client);
    if (serviceClientDeviceMethodHandle == NULL)
    {
        throw new std::runtime_error("IoTHubDeviceMethod_Create failed");
    }

    std::string methodName;
    std::string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);

    std::cout << "invoking " << methodName << std::endl;

    int responseStatus;
    unsigned char* responsePayload;
    size_t responsePayloadSize;
    IOTHUB_DEVICE_METHOD_RESULT invokeResult;
    if (moduleId.length() == 0)
    {
        invokeResult = IoTHubDeviceMethod_Invoke(serviceClientDeviceMethodHandle, deviceId.c_str(), methodName.c_str(), payload.c_str(), timeout, &responseStatus, &responsePayload, &responsePayloadSize);
    }
    else
    {
        invokeResult = IoTHubDeviceMethod_InvokeModule(serviceClientDeviceMethodHandle, deviceId.c_str(), moduleId.c_str(), methodName.c_str(), payload.c_str(), timeout, &responseStatus, &responsePayload, &responsePayloadSize);
    }

    std::cout << "Invoke returned.  Calling IoTHubDeviceMethod_Destroy..." << std::endl;
    IoTHubDeviceMethod_Destroy(serviceClientDeviceMethodHandle);

    if (invokeResult == IOTHUB_DEVICE_METHOD_OK)
    {
        std::cout << "method call succeeded" << std::endl;
        std::cout << "status = " << responseStatus << std::endl;
        std::string response((const char*)responsePayload, responsePayloadSize);
        std::cout << "response = " << response << std::endl;
        free(responsePayload);
        return makeInvokeResponse(responseStatus, response);
    }
    else
    {
        std::cout << "IoTHubDeviceMethod_Invoke failed with result " << invokeResult << std::endl;
        throw new std::runtime_error("IoTHubDeviceMethod_Invoke failed");
    }
}

std::string ServiceGlue::InvokeDeviceMethod(std::string connectionId, std::string deviceId, std::string methodInvokeParameters)
{
    std::cout << "InvokeDeviceMethod called for " << connectionId << " with deviceId " << deviceId << std::endl;
    std::cout << methodInvokeParameters << std::endl;
    return _invokeMethodCommon(connectionId, deviceId, std::string(), methodInvokeParameters);
}

std::string ServiceGlue::InvokeModuleMethod(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters)
{
    std::cout << "InvokeModuleMethod called for " << connectionId << " with deviceId " << deviceId << " and moduleId " << moduleId << std::endl;
    std::cout << methodInvokeParameters << std::endl;
    return _invokeMethodCommon(connectionId, deviceId, moduleId, methodInvokeParameters);
}

void ServiceGlue::CleanupResources()
{
    std::cout << "ServiceGlue::CleanupResources called" << std::endl;
    // copy the map since we're removing things from it while we're iterating over it.
    std::map<std::string, void*> mapCopy = this->clientMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        std::cout << "missed cleanup of " << iter->first << std::endl;
        this->Disconnect(iter->first);
    }
}

void sendC2dCallback(void* context, IOTHUB_MESSAGING_RESULT result)
{
    std::cout << "sendC2dCallback called with " << MU_ENUM_TO_STRING(IOTHUB_MESSAGING_RESULT, result) << std::endl;
    std::condition_variable *cv = (std::condition_variable *)context;
    cv->notify_one();
}

void ServiceGlue::SendC2dMessage(std::string connectionId, std::string deviceId, std::string eventBody)
{
    std::cout << "ServiceGlue::SendC2dMessage called for " << connectionId << " with deviceId " << deviceId << std::endl;
    IOTHUB_MESSAGING_CLIENT_HANDLE messaging_client = (IOTHUB_MESSAGING_CLIENT_HANDLE)this->messagingMap[connectionId];
    if (!messaging_client)
    {
        throw new std::runtime_error("client is not opened");
    }

    std::mutex m;
    std::condition_variable cv;

    IOTHUB_MESSAGE_HANDLE message = stringToMessage(eventBody);

    std::cout << "calling IoTHubMessaging_SendAsync" << std::endl;
    IOTHUB_MESSAGING_RESULT ret = IoTHubMessaging_SendAsync(messaging_client, deviceId.c_str(), message, sendC2dCallback, &cv);
    ThrowIfFailed(ret, "IoTHubMessaging_SendAsync");

    std::cout << "waiting for send confirmation" << std::endl;
    {
        std::unique_lock<std::mutex> lk(m);
        cv.wait(lk);
    }
    std::cout << "send confirmation received" << std::endl;
}
