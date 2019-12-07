/**
 * Azure IOT End-to-End Test Wrapper Rest Api
 * REST API definition for End-to-end testing of the Azure IoT SDKs.  All SDK APIs that are tested by our E2E tests need to be defined in this file.  This file takes some liberties with the API definitions.  In particular, response schemas are undefined, and error responses are also undefined.
 *
 * OpenAPI spec version: 1.0.0
 *
 *
 * NOTE: This class is auto generated by the swagger code generator 2.4.2.
 * https://github.com/swagger-api/swagger-codegen.git
 * Do not edit the class manually.
 */


#include <corvusoft/restbed/byte.hpp>
#include <corvusoft/restbed/string.hpp>
#include <corvusoft/restbed/settings.hpp>
#include <corvusoft/restbed/request.hpp>

#include "WrapperApi.h"

namespace io {
namespace swagger {
namespace server {
namespace api {

using namespace io::swagger::server::model;

WrapperApi::WrapperApi() {
	std::shared_ptr<WrapperApiWrapperCleanupResource> spWrapperApiWrapperCleanupResource = std::make_shared<WrapperApiWrapperCleanupResource>();
	this->publish(spWrapperApiWrapperCleanupResource);

	std::shared_ptr<WrapperApiWrapperCapabilitiesResource> spWrapperApiWrapperCapabilitiesResource = std::make_shared<WrapperApiWrapperCapabilitiesResource>();
	this->publish(spWrapperApiWrapperCapabilitiesResource);

	std::shared_ptr<WrapperApiWrapperMessageResource> spWrapperApiWrapperMessageResource = std::make_shared<WrapperApiWrapperMessageResource>();
	this->publish(spWrapperApiWrapperMessageResource);

	std::shared_ptr<WrapperApiWrapperCommandResource> spWrapperApiWrapperCommandResource = std::make_shared<WrapperApiWrapperCommandResource>();
	this->publish(spWrapperApiWrapperCommandResource);

	std::shared_ptr<WrapperApiWrapperFlagsResource> spWrapperApiWrapperFlagsResource = std::make_shared<WrapperApiWrapperFlagsResource>();
	this->publish(spWrapperApiWrapperFlagsResource);

}

WrapperApi::~WrapperApi() {}

void WrapperApi::startService(int const& port) {
	std::shared_ptr<restbed::Settings> settings = std::make_shared<restbed::Settings>();
	settings->set_port(port);
	settings->set_root("");

	this->start(settings);
}

void WrapperApi::stopService() {
	this->stop();
}

WrapperApiWrapperCleanupResource::WrapperApiWrapperCleanupResource()
{
	this->set_path("/wrapper/cleanup/");
	this->set_method_handler("PUT",
		std::bind(&WrapperApiWrapperCleanupResource::PUT_method_handler, this,
			std::placeholders::_1));
}

WrapperApiWrapperCleanupResource::~WrapperApiWrapperCleanupResource()
{
}

void WrapperApiWrapperCleanupResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();




			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

}



WrapperApiWrapperCapabilitiesResource::WrapperApiWrapperCapabilitiesResource()
{
	this->set_path("/wrapper/capabilities/");
	this->set_method_handler("GET",
		std::bind(&WrapperApiWrapperCapabilitiesResource::GET_method_handler, this,
			std::placeholders::_1));
}

WrapperApiWrapperCapabilitiesResource::~WrapperApiWrapperCapabilitiesResource()
{
}

void WrapperApiWrapperCapabilitiesResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();




			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

}



WrapperApiWrapperMessageResource::WrapperApiWrapperMessageResource()
{
	this->set_path("/wrapper/message/");
	this->set_method_handler("PUT",
		std::bind(&WrapperApiWrapperMessageResource::PUT_method_handler, this,
			std::placeholders::_1));
}

WrapperApiWrapperMessageResource::~WrapperApiWrapperMessageResource()
{
}

void WrapperApiWrapperMessageResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();
	// Body params are present, therefore we have to fetch them
	int content_length = request->get_header("Content-Length", 0);
	session->fetch(content_length,
		[ this ]( const std::shared_ptr<restbed::Session> session, const restbed::Bytes & body )
		{

			const auto request = session->get_request();
			std::string requestBody = restbed::String::format("%.*s\n", ( int ) body.size( ), body.data( ));
			/**
			 * Get body params or form params here from the requestBody string
			 */




			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

		});
}



WrapperApiWrapperCommandResource::WrapperApiWrapperCommandResource()
{
	this->set_path("/wrapper/command/");
	this->set_method_handler("PUT",
		std::bind(&WrapperApiWrapperCommandResource::PUT_method_handler, this,
			std::placeholders::_1));
}

WrapperApiWrapperCommandResource::~WrapperApiWrapperCommandResource()
{
}

void WrapperApiWrapperCommandResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();


			// Getting the query params
			const std::string cmd = request->get_query_parameter("cmd", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

}



WrapperApiWrapperFlagsResource::WrapperApiWrapperFlagsResource()
{
	this->set_path("/wrapper/flags/");
	this->set_method_handler("PUT",
		std::bind(&WrapperApiWrapperFlagsResource::PUT_method_handler, this,
			std::placeholders::_1));
}

WrapperApiWrapperFlagsResource::~WrapperApiWrapperFlagsResource()
{
}

void WrapperApiWrapperFlagsResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();
	// Body params are present, therefore we have to fetch them
	int content_length = request->get_header("Content-Length", 0);
	session->fetch(content_length,
		[ this ]( const std::shared_ptr<restbed::Session> session, const restbed::Bytes & body )
		{

			const auto request = session->get_request();
			std::string requestBody = restbed::String::format("%.*s\n", ( int ) body.size( ), body.data( ));
			/**
			 * Get body params or form params here from the requestBody string
			 */




			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

		});
}




}
}
}
}

