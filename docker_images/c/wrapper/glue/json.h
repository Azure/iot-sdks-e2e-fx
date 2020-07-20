// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.

#pragma once

#include <string>
#include <parson.h>


class Json {
public:
    Json();
    Json(std::string root_string);
    virtual ~Json();
  
    void loadFromString(std::string root_string);

    std::string getSubObject(std::string dotname);

    std::string getString(std::string dotname);
    double getNumber(std::string dotname);
    bool getBool(std::string dotname);

    std::string serializeToString();

    void setString(std::string dotname, std::string value);
    void setNumber(std::string dotname, double value);
    void setBool(std::string dotname, bool value);

private:
    void freeMemory();

    JSON_Value *m_root_value;
    JSON_Object *m_root_object;
};
