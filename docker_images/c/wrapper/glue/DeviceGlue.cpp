// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include "DeviceGlue.h"
#include "GlueUtils.h"


DeviceGlue::DeviceGlue()
{
}

DeviceGlue::~DeviceGlue()
{
}

std::string DeviceGlue::getNextClientId()
{
    static int clientCount = 0;
    static std::string client_prefix = "deviceClient_";
    return client_prefix + std::to_string(++clientCount);
}

void DeviceGlue::EnableC2dMessages(std::string connectionId)
{
    std::cout << "DeviceGlue::EnableC2dMessages for " << connectionId << std::endl;
    IOTHUB_DEVICE_CLIENT_HANDLE client = (IOTHUB_DEVICE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }
}

std::string DeviceGlue::WaitForC2dMessage(std::string connectionId)
{
    IOTHUB_CLIENT_RESULT ret;

    std::cout << "DeviceGlue::WaitForC2dMessage for " << connectionId << std::endl;
    IOTHUB_DEVICE_CLIENT_HANDLE client = (IOTHUB_DEVICE_CLIENT_HANDLE)this->clientMap[connectionId];
    if (!client)
    {
        throw new std::runtime_error("client is not opened");
    }

    message_response_struct resp;
    ret = IoTHubDeviceClient_SetMessageCallback(client, receiveMessageCallback, &resp);
    ThrowIfFailed(ret, "IoTHubDeviceClient_SetMessageCallback");

    std::cout << "waiting for message" << std::endl;
    try
    {
        std::unique_lock<std::mutex> lk(resp.m);
        resp.cv.wait(lk);
    }
    catch (...)
    {
        ret = IoTHubDeviceClient_SetMessageCallback(client, NULL, NULL);
        ThrowIfFailed(ret, "IoTHubDeviceClient_SetMessageCallback(NULL)");
        throw;
    }

    std::cout << "message received" << std::endl;
    ret = IoTHubDeviceClient_SetMessageCallback(client, NULL, NULL);
    ThrowIfFailed(ret, "IoTHubDeviceClient_SetMessageCallback(NULL)");

    return addJsonWrapperObject(resp.response_string, "body");
}
