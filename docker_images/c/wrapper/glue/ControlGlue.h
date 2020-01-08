// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <iostream>
#include <string>
#include <map>

class ControlGlue {
public:
    ControlGlue();
    virtual ~ControlGlue();

    void CleanupResources();
    void PrintMessage(const char* message);
    std::string GetCapabilities();
};