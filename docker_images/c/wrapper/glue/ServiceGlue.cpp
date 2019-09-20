// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <iostream>
#include "iothub_service_client_auth.h"
#include "iothub_devicemethod.h"
#include "ServiceGlue.h"
#include "GlueUtils.h"

using namespace std;

static int clientCount = 0;
static string client_prefix = "serviceClient_";

ServiceGlue::ServiceGlue()
{
}

ServiceGlue::~ServiceGlue()
{
}

string ServiceGlue::Connect(string connectionString)
{
    cout << "ServiceGlue::Connect called" << endl;
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client;

    if ((client = IoTHubServiceClientAuth_CreateFromConnectionString(connectionString.c_str())) == NULL)
    {
        throw new runtime_error("failed to create client");
    }
    else
    {
        string clientId = client_prefix + to_string(++clientCount);
        this->clientMap[clientId] = (void*)client;
        string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
        cout << "returning " << ret << endl;
        return ret;
    }
}

void ServiceGlue::Disconnect(string connectionId)
{
    cout << "ServiceGlue::Disconnect for " << connectionId << endl;
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = (IOTHUB_SERVICE_CLIENT_AUTH_HANDLE)this->clientMap[connectionId];
    if (client)
    {
        this->clientMap.erase(connectionId);
        cout << "calling IoTHubServiceClientAuth_Destroy" << endl;
        IoTHubServiceClientAuth_Destroy(client);
        cout << "done disconnecting" << endl;
    }
    else
    {
        cout << "client already closed.  nothing to do." << endl;
    }
}

string ServiceGlue::_invokeMethodCommon(string connectionId, string deviceId, string moduleId, string methodInvokeParameters)
{
    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = (IOTHUB_SERVICE_CLIENT_AUTH_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new runtime_error("client is not opened");
    }
    IOTHUB_SERVICE_CLIENT_DEVICE_METHOD_HANDLE serviceClientDeviceMethodHandle = IoTHubDeviceMethod_Create(client);
    if (serviceClientDeviceMethodHandle == NULL)
    {
        throw new runtime_error("IoTHubDeviceMethod_Create failed");
    }

    string methodName;
    string payload;
    unsigned int timeout;
    parseMethodInvokeParameters(methodInvokeParameters, &methodName, &payload, &timeout);

    cout << "invoking " << methodName << endl;

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

    cout << "Invoke returned.  Calling IoTHubDeviceMethod_Destroy..." << endl;
    IoTHubDeviceMethod_Destroy(serviceClientDeviceMethodHandle);

    if (invokeResult == IOTHUB_DEVICE_METHOD_OK)
    {
        cout << "method call succeeded" << endl;
        cout << "status = " << responseStatus << endl;
        string response((const char*)responsePayload, responsePayloadSize);
        cout << "response = " << response << endl;
        free(responsePayload);
        return makeInvokeResponse(responseStatus, response);
    }
    else
    {
        cout << "IoTHubDeviceMethod_Invoke failed with result " << invokeResult << endl;
        throw new runtime_error("IoTHubDeviceMethod_Invoke failed");
    }
}

string ServiceGlue::InvokeDeviceMethod(string connectionId, string deviceId, string methodInvokeParameters)
{
    cout << "InvokeDeviceMethod called for " << connectionId << " with deviceId " << deviceId << endl;
    cout << methodInvokeParameters << endl;
    return _invokeMethodCommon(connectionId, deviceId, string(), methodInvokeParameters);
}

string ServiceGlue::InvokeModuleMethod(string connectionId, string deviceId, string moduleId, string methodInvokeParameters)
{
    cout << "InvokeModuleMethod called for " << connectionId << " with deviceId " << deviceId << " and moduleId " << moduleId << endl;
    cout << methodInvokeParameters << endl;
    return _invokeMethodCommon(connectionId, deviceId, moduleId, methodInvokeParameters);
}

void ServiceGlue::CleanupResources()
{
    cout << "ServiceGlue::CleanupResources called" << endl;
    // copy the map since we're removing things from it while we're iterating over it.
    map<string, void*> mapCopy = this->clientMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        cout << "missed cleanup of " << iter->first << endl;
        this->Disconnect(iter->first);
    }
}

