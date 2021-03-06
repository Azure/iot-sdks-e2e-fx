/**
 * Azure IOT End-to-End Test Wrapper Rest Api
 * No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)
 *
 * OpenAPI spec version: 1.0.0
 *
 *
 * NOTE: This class is auto generated by the swagger code generator 2.4.2.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 */

/*
 * ControlApi.h
 *
 *
 */

#ifndef ControlApi_H_
#define ControlApi_H_


#include <memory>
#include <corvusoft/restbed/session.hpp>
#include <corvusoft/restbed/resource.hpp>
#include <corvusoft/restbed/service.hpp>

// Removed 3 lines in merge
// #include "LogMessage.h"
// #include "Object.h"
// #include <string>

namespace io {
namespace swagger {
namespace server {
namespace api {

// removed namespace in merge
// using namespace io::swagger::server::model;

// Made virtual in merge
class  ControlApi: public virtual restbed::Service
{
public:
	ControlApi();
	~ControlApi();
	void startService(int const& port);
	void stopService();
};


/// <summary>
/// verify that the clients have cleaned themselves up completely
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlCleanupResource: public restbed::Resource
{
public:
	ControlApiControlCleanupResource();
    virtual ~ControlApiControlCleanupResource();
    void PUT_method_handler(const std::shared_ptr<restbed::Session> session);
};

/// <summary>
/// Get capabilities for the objects in this server
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlCapabilitiesResource: public restbed::Resource
{
public:
	ControlApiControlCapabilitiesResource();
    virtual ~ControlApiControlCapabilitiesResource();
    void GET_method_handler(const std::shared_ptr<restbed::Session> session);
};

/// <summary>
/// Get statistics about the operation of the test wrapper
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlWrapperStatsResource: public restbed::Resource
{
public:
	ControlApiControlWrapperStatsResource();
    virtual ~ControlApiControlWrapperStatsResource();
    void GET_method_handler(const std::shared_ptr<restbed::Session> session);
};

/// <summary>
/// log a message to output
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlMessageResource: public restbed::Resource
{
public:
	ControlApiControlMessageResource();
    virtual ~ControlApiControlMessageResource();
    void PUT_method_handler(const std::shared_ptr<restbed::Session> session);
};

/// <summary>
/// send an arbitrary command
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlCommandResource: public restbed::Resource
{
public:
	ControlApiControlCommandResource();
    virtual ~ControlApiControlCommandResource();
    void PUT_method_handler(const std::shared_ptr<restbed::Session> session);
};

/// <summary>
/// set flags for the objects in this server to use
/// </summary>
/// <remarks>
///
/// </remarks>
class  ControlApiControlFlagsResource: public restbed::Resource
{
public:
	ControlApiControlFlagsResource();
    virtual ~ControlApiControlFlagsResource();
    void PUT_method_handler(const std::shared_ptr<restbed::Session> session);
};


}
}
}
}

#endif /* ControlApi_H_ */

