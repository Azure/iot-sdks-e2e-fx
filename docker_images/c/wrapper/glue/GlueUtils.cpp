// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include <iostream>
#include <mutex>
#include <condition_variable>
#include <stdexcept>
#include "GlueUtils.h"
#include "json.h"

static const char* const PARSON_ERROR = "parson error";

#ifndef MU_ENUM_TO_STRING
#define MU_ENUM_TO_STRING ENUM_TO_STRING
#endif

void ThrowIfFailed(IOTHUB_CLIENT_RESULT ret, std::string functionName)
{
    if (ret != IOTHUB_CLIENT_OK)
    {
        throw new std::runtime_error(std::string(functionName) + " returned " + MU_ENUM_TO_STRING(IOTHUB_CLIENT_RESULT, ret));
    }
}

void ThrowIfFailed(IOTHUB_MESSAGING_RESULT ret, std::string functionName)
{
    if (ret != IOTHUB_MESSAGING_OK)
    {
        throw new std::runtime_error(std::string(functionName) + " returned " + MU_ENUM_TO_STRING(IOTHUB_MESSAGING_RESULT, ret));
    }
}


IOTHUB_CLIENT_TRANSPORT_PROVIDER protocolFromTransportName(std::string transportType)
{
    if (strcmp(transportType.c_str(), "mqtt") == 0)
    {
        return MQTT_Protocol;
    }
    else if (strcmp(transportType.c_str(), "mqttws") == 0)
    {
        return MQTT_WebSocket_Protocol;
    }
    else if (strcmp(transportType.c_str(), "amqp") == 0)
    {
        return AMQP_Protocol;
    }
    else if (strcmp(transportType.c_str(), "amqpws") == 0)
    {
        return AMQP_Protocol_over_WebSocketsTls;
    }
    else
    {
        std::string transport_string = "Unknown transport: ";
        throw new std::runtime_error(transport_string + transportType);
    }
}


void parseMethodInvokeParameters(std::string methodInvokeParameters, std::string *methodName, std::string *payload, unsigned int *timeout)
{
    Json json(methodInvokeParameters);

    *methodName = json.getString("methodName");
    *payload = json.getSubObject("payload");
    *timeout = (unsigned int)json.getNumber("responseTimeoutInSeconds");
}

std::string makeInvokeResponse(int statusCode, std::string payload)
{
    Json json;
    json.setNumber("status", (double)statusCode);
    json.setString("payload", payload);
    return json.serializeToString();
}


void parseMethodRequestAndResponse(std::string requestAndResponse, std::string *expectedRequest, std::string *response, int *statusCode)
{
    Json json(requestAndResponse);
    *expectedRequest = json.getSubObject("requestPayload.payload");
    *response = json.getSubObject("responsePayload");
    *statusCode = (int)json.getNumber("statusCode");
}


std::string addJsonWrapperObject(std::string old_root_string, std::string wrapperDotname)
{
    JSON_Value* old_root_value = NULL;
    JSON_Value* new_root_value = NULL;
    char *new_string = NULL;
    
    try
    {
        JSON_Object* new_root_object;
        if ((old_root_value = json_parse_string(old_root_string.c_str())) == NULL)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }
        else if ((new_root_value = json_value_init_object()) == NULL)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }
        else if ((new_root_object = json_value_get_object(new_root_value)) == NULL)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }
        else if (json_object_dotset_value(new_root_object, wrapperDotname.c_str(), old_root_value) != JSONSuccess)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }

        new_string = json_serialize_to_string(new_root_value);
        std::string result = new_string;
        json_free_serialized_string(new_string);
        new_string = NULL;

        json_value_free(new_root_value); //implicitly frees old_root_value and new_root_object as well
        new_root_value = NULL;

        return result;
    }
    catch (...)
    {
        if (new_string)
        {
            json_free_serialized_string(new_string);
            new_string = NULL;
        }

        if (old_root_value)
        {
            json_value_free(old_root_value);
            old_root_value = NULL;
        }

        if (new_root_value)
        {
            json_value_free(new_root_value); //implicitly frees new_root_object as well
            new_root_value = NULL;
        }

        throw;
    }
}

IOTHUB_MESSAGE_HANDLE stringToMessage(std::string eventBody)
{
    return IoTHubMessage_CreateFromString(Json(eventBody).getSubObject("body").c_str());
}

void sendEventCallback(IOTHUB_CLIENT_CONFIRMATION_RESULT result, void *userContextCallback)
{
    std::cout << "sendEventCallback called with " << MU_ENUM_TO_STRING(IOTHUB_CLIENT_CONFIRMATION_RESULT, result) << std::endl;
    std::condition_variable *cv = (std::condition_variable *)userContextCallback;
    cv->notify_one();
}


