// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
#include "json.h"
#include <stdexcept>

using namespace std;

static const char* const PARSON_ERROR = "parson error";

Json::Json()
    :Json("{}")
{
}

Json::Json(std::string root_string)
{
    this->m_root_value = NULL;
    this->m_root_object = NULL;
    this->loadFromString(root_string);
}

Json::~Json()
{
    this->freeMemory();
}

void Json::freeMemory()
{
    if (this->m_root_value) 
    {
        json_value_free(this->m_root_value); //implicitly frees m_root_object as well
        this->m_root_value = NULL;
        this->m_root_object = NULL;
    }
}

void Json::loadFromString(std::string root_string)
{
    this->freeMemory();
    try
    {
        if ((this->m_root_value = json_parse_string(root_string.c_str())) == NULL)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }
        else if ((this->m_root_object = json_value_get_object(this->m_root_value)) == NULL)
        {
            throw new std::runtime_error(PARSON_ERROR);
        }
    }
    catch (...)
    {
        this->freeMemory();
        throw;
    }
}

std::string Json::getSubObject(std::string dotname)
{
    JSON_Value *subObject;
    char *subString;
    if ((subObject = json_object_dotget_value(this->m_root_object, dotname.c_str())) == NULL)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
    if ((subString = json_serialize_to_string(subObject)) == NULL)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
    string result = subString;
    json_free_serialized_string(subString);
    return result;
}

std::string Json::serializeToString()
{
    char *str = json_serialize_to_string(this->m_root_value);
    string result = str;
    json_free_serialized_string(str);
    return result;
}

double Json::getNumber(std::string dotname)
{
    return json_object_dotget_number(this->m_root_object, dotname.c_str());
}

void Json::setNumber(std::string dotname, double value)
{
    if (json_object_dotset_number(this->m_root_object, dotname.c_str(), value) != JSONSuccess)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
}


std::string Json::getString(std::string dotname)
{
    const char *str;
    if ((str = json_object_dotget_string(this->m_root_object, dotname.c_str())) == NULL)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
    string result = str;
    return result;
}

void Json::setString(std::string dotname, std::string value)
{
    if (json_object_dotset_string(this->m_root_object, dotname.c_str(), value.c_str()) != JSONSuccess)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
}

bool Json::getBool(std::string dotname)
{
    return !!json_object_dotget_boolean(this->m_root_object, dotname.c_str());
}

void Json::setBool(std::string dotname, bool value)
{
    if (json_object_dotset_boolean(this->m_root_object, dotname.c_str(), value ? 1 : 0) != JSONSuccess)
    {
        throw new std::runtime_error(PARSON_ERROR);
    }
}

