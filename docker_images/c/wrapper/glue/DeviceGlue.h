// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <iostream>
#include <string>
#include <map>
#include "InternalGlue.h"


class DeviceGlue : public InternalGlue {
public:
    DeviceGlue();
    virtual ~DeviceGlue();

    void EnableC2dMessages(std::string connectionId);
    std::string WaitForC2dMessage(std::string connectionId);

private:
    virtual std::string getNextClientId();
};
