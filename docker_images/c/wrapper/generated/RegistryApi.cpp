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


#include <corvusoft/restbed/byte.hpp>
#include <corvusoft/restbed/string.hpp>
#include <corvusoft/restbed/settings.hpp>
#include <corvusoft/restbed/request.hpp>

#include "RegistryApi.h"


namespace io {
namespace swagger {
namespace server {
namespace api {

// removed namespace in merge
// using namespace io::swagger::server::model;

RegistryApi::RegistryApi() {
	std::shared_ptr<RegistryApiRegistryConnectResource> spRegistryApiRegistryConnectResource = std::make_shared<RegistryApiRegistryConnectResource>();
	this->publish(spRegistryApiRegistryConnectResource);

	std::shared_ptr<RegistryApiRegistryConnectionIdDisconnectResource> spRegistryApiRegistryConnectionIdDisconnectResource = std::make_shared<RegistryApiRegistryConnectionIdDisconnectResource>();
	this->publish(spRegistryApiRegistryConnectionIdDisconnectResource);

	std::shared_ptr<RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource> spRegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource = std::make_shared<RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource>();
	this->publish(spRegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource);

	std::shared_ptr<RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource> spRegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource = std::make_shared<RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource>();
	this->publish(spRegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource);

}

RegistryApi::~RegistryApi() {}

void RegistryApi::startService(int const& port) {
	std::shared_ptr<restbed::Settings> settings = std::make_shared<restbed::Settings>();
	settings->set_port(port);
	settings->set_root("");

	this->start(settings);
}

void RegistryApi::stopService() {
	this->stop();
}

RegistryApiRegistryConnectResource::RegistryApiRegistryConnectResource()
{
	this->set_path("/registry/connect/");
	this->set_method_handler("PUT",
		std::bind(&RegistryApiRegistryConnectResource::PUT_method_handler, this,
			std::placeholders::_1));
}

RegistryApiRegistryConnectResource::~RegistryApiRegistryConnectResource()
{
}

void RegistryApiRegistryConnectResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();


			// Getting the query params
			const std::string connectionString = request->get_query_parameter("connectionString", "");

			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

}



RegistryApiRegistryConnectionIdDisconnectResource::RegistryApiRegistryConnectionIdDisconnectResource()
{
	this->set_path("/registry/{connectionId: .*}/disconnect//");
	this->set_method_handler("PUT",
		std::bind(&RegistryApiRegistryConnectionIdDisconnectResource::PUT_method_handler, this,
			std::placeholders::_1));
}

RegistryApiRegistryConnectionIdDisconnectResource::~RegistryApiRegistryConnectionIdDisconnectResource()
{
}

void RegistryApiRegistryConnectionIdDisconnectResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				// removed "OK" in merge
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

}



RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource()
{
	this->set_path("/registry/{connectionId: .*}/deviceTwin/{deviceId: .*}/");
	this->set_method_handler("GET",
		std::bind(&RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::GET_method_handler, this,
			std::placeholders::_1));
	this->set_method_handler("PATCH",
		std::bind(&RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::PATCH_method_handler, this,
			std::placeholders::_1));
}

RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::~RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource()
{
}

void RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");
			const std::string deviceId = request->get_path_parameter("deviceId", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				// Changed one paramter in merge
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

}

void RegistryApiRegistryConnectionIdDeviceTwinDeviceIdResource::PATCH_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();
	// Body params are present, therefore we have to fetch them
	int content_length = request->get_header("Content-Length", 0);
	session->fetch(content_length,
		[ this ]( const std::shared_ptr<restbed::Session> session, const restbed::Bytes & body )
		{

			const auto request = session->get_request();
			std::string requestBody = restbed::String::format("%.*s\n", ( int ) body.size( ), body.data( ));

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");
			const std::string deviceId = request->get_path_parameter("deviceId", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				// removed "OK" in merge
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

		});
}


RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource()
{
	this->set_path("/registry/{connectionId: .*}/moduleTwin/{deviceId: .*}/{moduleId: .*}/");
	this->set_method_handler("GET",
		std::bind(&RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::GET_method_handler, this,
			std::placeholders::_1));
	this->set_method_handler("PATCH",
		std::bind(&RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::PATCH_method_handler, this,
			std::placeholders::_1));
}

RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::~RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource()
{
}

void RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");
			const std::string deviceId = request->get_path_parameter("deviceId", "");
			const std::string moduleId = request->get_path_parameter("moduleId", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				// changed 1 parameter in merge
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

}

void RegistryApiRegistryConnectionIdModuleTwinDeviceIdModuleIdResource::PATCH_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();
	// Body params are present, therefore we have to fetch them
	int content_length = request->get_header("Content-Length", 0);
	session->fetch(content_length,
		[ this ]( const std::shared_ptr<restbed::Session> session, const restbed::Bytes & body )
		{

			const auto request = session->get_request();
			std::string requestBody = restbed::String::format("%.*s\n", ( int ) body.size( ), body.data( ));

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");
			const std::string deviceId = request->get_path_parameter("deviceId", "");
			const std::string moduleId = request->get_path_parameter("moduleId", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */

			if (status_code == 200) {
				// removed "OK" in merge
				session->close(200, "", { {"Connection", "close"} });
				return;
			}

		});
}



}
}
}
}

