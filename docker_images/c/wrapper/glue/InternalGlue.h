// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once
#include <string>
#include <map>
#include <mutex>
#include <condition_variable>
#include <iostream>

#include "iothub_sdk.h"

struct twin_callback_struct
{
    std::condition_variable cv;
    std::mutex m;
    std::condition_variable cvp;
    std::mutex mp;
    std::string latest_payload;
    std::string current_complete;
};

struct message_response_struct
{
    std::mutex m;
    std::condition_variable cv;
    std::string response_string;
};

struct method_callback_struct
{
    std::mutex m;
    std::condition_variable cv;
    std::string expected_method_name;
    std::string expected_request_payload;
    std::string actual_method_name;
    std::string actual_request_payload;
    std::string response;
    int status_code;
};

struct method_invoke_response
{
    std::mutex m;
    std::condition_variable cv;
    int statusCode;
    std::string payload;
};


IOTHUBMESSAGE_DISPOSITION_RESULT receiveMessageCallback(IOTHUB_MESSAGE_HANDLE message, void *userContextCallback);

void setConnectionStatusCallback(IOTHUB_CLIENT_CORE_HANDLE);
static void connectionStatusCallback(IOTHUB_CLIENT_CONNECTION_STATUS, IOTHUB_CLIENT_CONNECTION_STATUS_REASON, void *);

class InternalGlue 
{
public:
    InternalGlue();
    virtual ~InternalGlue();

    std::string Connect(const char *transportType, std::string connectionString, std::string caCertificate);
    void Disconnect(std::string connectionId);
    void EnableMethods(std::string connectionId);
    void EnableTwin(std::string connectionId);
    void SendEvent(std::string connectionId, std::string eventBody);
    void WaitForMethodAndReturnResponse(std::string connectionId, std::string methodName, std::string requestAndResponse);
    std::string WaitForDesiredPropertyPatch(std::string connectionId);
    std::string GetTwin(std::string connectionId);
    void SendTwinPatch(std::string connectionId, std::string props);
    void CleanupResources();

protected:
    virtual std::string getNextClientId() = 0;
    std::map<std::string, void*> clientMap;
    std::map<std::string, void*> twinMap;
};
