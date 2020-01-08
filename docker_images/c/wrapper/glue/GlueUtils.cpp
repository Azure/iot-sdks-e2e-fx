// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include "GlueUtils.h"
#include <stdexcept>

using namespace std;

static const char* const PARSON_ERROR = "parson error";

string getJsonString(JSON_Object* root_object, string dotname)
{
    const char *str;
    if ((str = json_object_dotget_string(root_object, dotname.c_str())) == NULL)
    {
        throw new runtime_error(PARSON_ERROR);
    }
    string result = str;
    return result;
}

string getJsonObjectAsString(JSON_Object* root_object, string dotname)
{
    JSON_Value *subObject;
    char *subString;
    if ((subObject = json_object_dotget_value(root_object, dotname.c_str())) == NULL)
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

string getJsonSubObject(string root_string, string dotname)
{
    JSON_Value *root_value = NULL;

    try
    {
        JSON_Object *root_object;
        string sub_object;

        if ((root_value = json_parse_string(root_string.c_str())) == NULL)
        {
            throw new runtime_error("parson error");
        }
        else if ((root_object = json_value_get_object(root_value)) == NULL)
        {
            throw new runtime_error("parson error");
        }

        sub_object = getJsonObjectAsString(root_object, dotname.c_str());
        json_value_free(root_value); //implicitly frees root_object as well
        
        return sub_object;
    }
    catch (...)
    {
        if (root_value)
        {
            json_value_free(root_value); //implicitly frees root_object as well
        }
        throw;

    }
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
            throw new runtime_error(PARSON_ERROR);
        }
        else if ((new_root_value = json_value_init_object()) == NULL)
        {
            throw new runtime_error(PARSON_ERROR);
        }
        else if ((new_root_object = json_value_get_object(new_root_value)) == NULL)
        {
            throw new runtime_error(PARSON_ERROR);
        }
        else if (json_object_dotset_value(new_root_object, wrapperDotname.c_str(), old_root_value) != JSONSuccess)
        {
            throw new runtime_error(PARSON_ERROR);
        }

        new_string = json_serialize_to_string(new_root_value);
        string result = new_string;
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
