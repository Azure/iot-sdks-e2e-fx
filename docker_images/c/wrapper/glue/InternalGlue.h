// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include <map>


class InternalGlue 
{
public:
    InternalGlue();
    virtual ~InternalGlue();

    std::string Connect(const char *transportType, std::string connectionString, std::string caCertificate);
    std::string ConnectFromEnvironment(const char *transportType);
    void Disconnect(std::string connectionId);
    void EnableInputMessages(std::string connectionId);
    void EnableMethods(std::string connectionId);
    void EnableTwin(std::string connectionId);
    void SendEvent(std::string connectionId, std::string eventBody);
    void SendOutputEvent(std::string connectionId, std::string outputName, std::string eventBody);
    std::string WaitForInputMessage(std::string connectionId, std::string inputName);
    void WaitForMethodAndReturnResponse(std::string connectionId, std::string methodName, std::string requestAndResponse);
    std::string InvokeModuleMethod(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters);
    std::string InvokeDeviceMethod(std::string connectionId, std::string deviceId, std::string methodInvokeParameters);
    std::string WaitForDesiredPropertyPatch(std::string connectionId);
    std::string GetTwin(std::string connectionId);
    void SendTwinPatch(std::string connectionId, std::string props);
    void CleanupResources();

private:
    virtual std::string getNextClientId() = 0;
    std::map<std::string, void*> clientMap;
    std::map<std::string, void*> twinMap;
};