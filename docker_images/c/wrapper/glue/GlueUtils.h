// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once

#include <string>
#include <parson.h>


std::string getJsonString(JSON_Object* root_object, std::string dotname);
std::string getJsonObjectAsString(JSON_Object* root_object, std::string dotname);
void parseMethodInvokeParameters(std::string methodInvokeParameters, std::string *methodName, std::string *payload, unsigned int *timeout);
std::string makeInvokeResponse(int statusCode, std::string payload);
std::string getJsonSubObject(std::string root_string, std::string dotname);
std::string addJsonWrapperObject(std::string root_string, std::string wrapperName);