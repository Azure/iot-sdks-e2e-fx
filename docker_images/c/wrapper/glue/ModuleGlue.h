// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include "InternalGlue.h"


class ModuleGlue : public InternalGlue {
public:
    ModuleGlue();
    virtual ~ModuleGlue();

    std::string ConnectFromEnvironment(const char *transportType);
    void EnableInputMessages(std::string connectionId);
    void SendOutputEvent(std::string connectionId, std::string outputName, std::string eventBody);
    std::string WaitForInputMessage(std::string connectionId, std::string inputName);
    std::string InvokeModuleMethod(std::string connectionId, std::string deviceId, std::string moduleId, std::string methodInvokeParameters);
    std::string InvokeDeviceMethod(std::string connectionId, std::string deviceId, std::string methodInvokeParameters);

private:
    virtual std::string getNextClientId();
};
