// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#include <iostream>
#include "ControlGlue.h"
#include "ModuleGlue.h"
#include "RegistryGlue.h"
#include "ServiceGlue.h"

using namespace std;

extern ModuleGlue module_glue;
extern RegistryGlue registry_glue;
extern ServiceGlue service_glue;

ControlGlue::ControlGlue()
{
}

ControlGlue::~ControlGlue()
{
}

void ControlGlue::CleanupResources()
{
    try
    {
        module_glue.CleanupResources();
    }
    catch (runtime_error)
    {
        cout << "Ignoring exception on module cleanup" << endl;
    }
    try
    {
        service_glue.CleanupResources();
    }
    catch (runtime_error)
    {
        cout << "Ignoring exception on service cleanup" << endl;
    }
    try
    {
        registry_glue.CleanupResources();
    }
    catch (runtime_error)
    {
        cout << "Ignoring exception on registry cleanup" << endl;
    }
}


void ControlGlue::PrintMessage(const char* message)
{
    cout << message;
}

std::string ControlGlue::GetCapabilities()
{
    return "{ " \
            "\"flags\": { " \
                "\"v2_connect_group\" : false, " \
                "\"dropped_connection_tests\" : false, " \
                "\"net_control_app\" : false " \
            "} " \
        "} ";
}


