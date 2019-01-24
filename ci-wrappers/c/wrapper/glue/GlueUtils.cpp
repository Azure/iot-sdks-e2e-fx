// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include "GlueUtils.h"
#include <stdexcept>

using namespace std;

static const char* const PARSON_ERROR = "parson error";

string getJsonString(JSON_Object* root_object, const char* dotname)
{
    const char *str;
    if ((str = json_object_dotget_string(root_object, dotname)) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    string result = str;
    return result;
}

string getJsonObjectAsString(JSON_Object* root_object, const char* dotname)
{
    JSON_Value *subObject;
    char *subString;
    if ((subObject = json_object_dotget_value(root_object, dotname)) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    if ((subString = json_serialize_to_string(subObject)) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    string result = subString;
    json_free_serialized_string(subString);
    return result;
}

void parseMethodInvokeParameters(string methodInvokeParameters, string *methodName, string *payload, unsigned int *timeout)
{
    JSON_Value* root_value;
    JSON_Object* root_object;
    if ((root_value = json_parse_string(methodInvokeParameters.c_str())) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    else if ((root_object = json_value_get_object(root_value)) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    *methodName = getJsonString(root_object, "methodName");
    *payload = getJsonObjectAsString(root_object, "payload");
    *timeout = (unsigned int)json_object_get_number(root_object, "responseTimeoutInSeconds");

    json_value_free(root_value); //implicitly frees root_object as well
}

string makeInvokeResponse(int statusCode, string payload)
{
    JSON_Value* root_value;
    JSON_Object* root_object;
    if ((root_value = json_parse_string("{}")) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    else if ((root_object = json_value_get_object(root_value)) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    else if (json_object_set_number(root_object, "status", (double)statusCode) != JSONSuccess)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    else if (json_object_set_string(root_object, "payload", payload.c_str()) != JSONSuccess)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    char *str = json_serialize_to_string(root_value);
    string result = str;
    json_free_serialized_string(str);
    return result;
}

