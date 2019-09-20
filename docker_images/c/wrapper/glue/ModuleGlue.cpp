// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include <string>
#include <mutex>
#include <condition_variable>

#define USE_EDGE_MODULES
#define USE_PROV_MODULE
#include "internal/iothub_client_edge.h"
#include "iothub_module_client.h"
#include "iothubtransportamqp.h"
#include "iothubtransporthttp.h"
#include "iothubtransportmqtt.h"
#include "iothub.h"
#include "parson.h"

#include "GlueUtils.h"
#include "ModuleGlue.h"

using namespace std;

static int clientCount = 0;
static string client_prefix = "moduleClient_";

ModuleGlue::ModuleGlue()
{
    IoTHub_Init();
}

ModuleGlue::~ModuleGlue()
{
}

string ModuleGlue::getNextClientId()
{
    static int clientCount = 0;
    static string client_prefix = "moduleClient_";
    return client_prefix + std::to_string(++clientCount);
}
