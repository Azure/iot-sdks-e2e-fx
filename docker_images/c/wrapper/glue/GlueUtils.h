// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once

#include <string>
#include "iothub_sdk.h"

void ThrowIfFailed(IOTHUB_CLIENT_RESULT ret, std::string functionName);
void ThrowIfFailed(IOTHUB_MESSAGING_RESULT ret, std::string functionName);

IOTHUB_CLIENT_TRANSPORT_PROVIDER protocolFromTransportName(std::string transportType);
IOTHUB_MESSAGE_HANDLE stringToMessage(std::string eventBody);

void parseMethodInvokeParameters(std::string methodInvokeParameters, std::string *methodName, std::string *payload, unsigned int *timeout);
void parseMethodRequestAndResponse(std::string requestAndResponse, std::string *expectedRequest, std::string *response, int *statusCode);
std::string makeInvokeResponse(int statusCode, std::string payload);
std::string addJsonWrapperObject(std::string root_string, std::string wrapperName);

void sendEventCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void *userContextCallback);
