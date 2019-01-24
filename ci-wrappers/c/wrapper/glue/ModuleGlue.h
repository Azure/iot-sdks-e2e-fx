// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include "InternalGlue.h"


class ModuleGlue : public InternalGlue {
public:
    ModuleGlue();
    virtual ~ModuleGlue();

private:
    virtual std::string getNextClientId();
};