// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include <map>


class ServiceGlue {
public:
    ServiceGlue();
    virtual ~ServiceGlue();

    std::string Connect(std::string connectionString);
    void Disconnect(std::string connectionId);
    std::string InvokeDeviceMethod(std::string connectionId, std::string deviceId, std::string methodInvokeParameters);
    std::string InvokeModuleMethod(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters);
    void SendC2dMessage(std::string connectionId, std::string deviceId, std::string eventBody);

    void CleanupResources();

private:
    std::string _invokeMethodCommon(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters);
    std::map<std::string, void*> clientMap;
    std::map<std::string, void*> messagingMap;
};
