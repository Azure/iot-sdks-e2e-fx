// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <iostream>
#include "RegistryGlue.h"
#include "iothub_service_client_auth.h"
#include "iothub_devicetwin.h"
#include "GlueUtils.h"

using namespace std;

static int clientCount = 0;
static string client_prefix = "registryClient_";

RegistryGlue::RegistryGlue()
{
}

RegistryGlue::~RegistryGlue()
{
}

string RegistryGlue::Connect(string connectionString)
{
    cout << "RegistryGlue::Connect called" << endl;

    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client;
    IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE twin;

    if ((client = IoTHubServiceClientAuth_CreateFromConnectionString(connectionString.c_str())) == NULL)
    {
        throw new runtime_error("failed to create client");
    }
    if ((twin = IoTHubDeviceTwin_Create(client)) == NULL)
    {
        IoTHubServiceClientAuth_Destroy(client);
        throw new runtime_error("failed to create twin");
    }

    string clientId = client_prefix + to_string(++clientCount);
    this->clientMap[clientId] = (void*)client;
    this->twinMap[clientId] = (void*)twin;
    string ret = "{ \"connectionId\" : \"" + clientId + "\"}";
    cout << "returning " << ret << endl;
    return ret;
}

void RegistryGlue::Disconnect(string connectionId)
{
    cout << "RegistryGlue::Disconnect for " << connectionId << endl;

    IOTHUB_SERVICE_CLIENT_AUTH_HANDLE client = (IOTHUB_SERVICE_CLIENT_AUTH_HANDLE)this->clientMap[connectionId];
    IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE twin = (IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE)this->twinMap[connectionId];

    if (twin)
    {
        this->twinMap.erase(connectionId);
        cout << "calling IoTHubDeviceTwin_Destroy" << endl;
        IoTHubDeviceTwin_Destroy(twin);
        cout << "done destroying twin" << endl;
    }
    else
    {
        cout << "twin already destroyed.  nothing to do." << endl;
    }

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

string RegistryGlue::GetModuleTwin(string connectionId, string deviceId, string moduleId)
{
    cout << "GetModuletwin called for deviceid = " << deviceId << " and moduleId " << moduleId << endl;

    IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE twin = (IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE)this->twinMap[connectionId];
    if (!twin)
    {
        throw new runtime_error("client is not opened");
    }


    char* deviceTwinJson;
    cout << "Calling IoTHubDeviceTwin_GetModuleTwin" << endl;
    if ((deviceTwinJson = IoTHubDeviceTwin_GetModuleTwin(twin, deviceId.c_str(), moduleId.c_str())) == NULL)
    {
        throw new runtime_error("IoTHubDeviceTwin_GetDeviceTwin failed");
    }
    string result = deviceTwinJson;
    free(deviceTwinJson);
    cout << "device twin: " << result << endl;
    return getJsonSubObject(result, "properties");
}

void RegistryGlue::PatchModuleTwin(string connectionId, string deviceId, string moduleId, string patch)
{
    cout << "patchModuleTwin called for deviceid = " << deviceId << " and moduleId " << moduleId << endl;
    cout << patch << endl;

    IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE twin = (IOTHUB_SERVICE_CLIENT_DEVICE_TWIN_HANDLE)this->twinMap[connectionId];
    if (!twin)
    {
        throw new runtime_error("client is not opened");
    }

    string wrappedPatch = addJsonWrapperObject(patch, "properties");
    char* deviceTwinJson;
    cout << "calling IoTHubDeviceTwin_UpdateModuleTwin" << endl;
    if ((deviceTwinJson = IoTHubDeviceTwin_UpdateModuleTwin(twin, deviceId.c_str(), moduleId.c_str(), wrappedPatch.c_str())) == NULL)
    {
        throw new runtime_error("IoTHubDeviceTwin_UpdateModuleTwin failed");
    }
    cout << "Updated twin:" << deviceTwinJson << endl;
    free(deviceTwinJson);
}

void RegistryGlue::CleanupResources()
{
    cout << "RegistryGlue::CleanupResources called" << endl;
    // copy the map since we're removing things from it while we're iterating over it.
    map<string, void*> mapCopy = this->clientMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        cout << "missed cleanup of " << iter->first << endl;
        this->Disconnect(iter->first);
    }
    // Now, go through the twin map just in case something was really messed up.
    mapCopy = this->twinMap;
    for (auto iter = mapCopy.begin(); iter != mapCopy.end(); ++iter)
    {
        cout << "missed cleanup of twin " << iter->first << endl;
        this->Disconnect(iter->first);
    }

}

