// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include <map>

class RegistryGlue {
public:
    RegistryGlue();
    virtual ~RegistryGlue();

    std::string Connect(std::string connectionString);
    void Disconnect(std::string connectionId);
    std::string GetModuleTwin(std::string connectionId, std::string deviceId, std::string moduleId);
    void PatchModuleTwin(std::string connectionId, std::string deviceId, std::string moduleId, std::string patch);

    void CleanupResources();

private:
    std::map<std::string, void*> clientMap;
    std::map<std::string, void*> twinMap;

};