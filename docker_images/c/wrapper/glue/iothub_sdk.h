
// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once

#define USE_EDGE_MODULES
#define USE_PROV_MODULE
#include "internal/iothub_client_edge.h"
#include "iothub_device_client.h"
#include "iothub_module_client.h"
#include "iothub_client_options.h"
#include "iothubtransportamqp.h"
#include "iothubtransportamqp_websockets.h"
#include "iothubtransportmqtt.h"
#include "iothubtransportmqtt_websockets.h"
#include "iothub.h"

#include "iothub_service_client_auth.h"
#include "iothub_devicemethod.h"
#include "iothub_messaging.h"
