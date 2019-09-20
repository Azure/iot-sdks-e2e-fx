// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include <string>
#include <mutex>
#include <condition_variable>

#define USE_EDGE_MODULES
#define USE_PROV_MODULE
#include "internal/iothub_client_edge.h"
#include "iothub_module_client.h"
#include "iothub.h"
#include "parson.h"

#include "GlueUtils.h"
#include "DeviceGlue.h"

using namespace std;


DeviceGlue::DeviceGlue()
{
}

DeviceGlue::~DeviceGlue()
{
}

string DeviceGlue::getNextClientId()
{
    static int clientCount = 0;
    static string client_prefix = "deviceClient_";
    return client_prefix + to_string(++clientCount);
}
