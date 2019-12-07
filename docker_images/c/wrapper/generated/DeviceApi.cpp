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

#include "DeviceApi.h"

// Added 2 lines in merge 
#include "DeviceGlue.h"
DeviceGlue device_glue;

namespace io {
namespace swagger {
namespace server {
namespace api {

// removed namespace in merge
// using namespace io::swagger::server::model;

DeviceApi::DeviceApi() {
	std::shared_ptr<DeviceApiDeviceConnectTransportTypeResource> spDeviceApiDeviceConnectTransportTypeResource = std::make_shared<DeviceApiDeviceConnectTransportTypeResource>();
	this->publish(spDeviceApiDeviceConnectTransportTypeResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdConnect2Resource> spDeviceApiDeviceConnectionIdConnect2Resource = std::make_shared<DeviceApiDeviceConnectionIdConnect2Resource>();
	this->publish(spDeviceApiDeviceConnectionIdConnect2Resource);

	std::shared_ptr<DeviceApiDeviceCreateFromConnectionStringTransportTypeResource> spDeviceApiDeviceCreateFromConnectionStringTransportTypeResource = std::make_shared<DeviceApiDeviceCreateFromConnectionStringTransportTypeResource>();
	this->publish(spDeviceApiDeviceCreateFromConnectionStringTransportTypeResource);

	std::shared_ptr<DeviceApiDeviceCreateFromX509TransportTypeResource> spDeviceApiDeviceCreateFromX509TransportTypeResource = std::make_shared<DeviceApiDeviceCreateFromX509TransportTypeResource>();
	this->publish(spDeviceApiDeviceCreateFromX509TransportTypeResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdDestroyResource> spDeviceApiDeviceConnectionIdDestroyResource = std::make_shared<DeviceApiDeviceConnectionIdDestroyResource>();
	this->publish(spDeviceApiDeviceConnectionIdDestroyResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdDisconnectResource> spDeviceApiDeviceConnectionIdDisconnectResource = std::make_shared<DeviceApiDeviceConnectionIdDisconnectResource>();
	this->publish(spDeviceApiDeviceConnectionIdDisconnectResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdDisconnect2Resource> spDeviceApiDeviceConnectionIdDisconnect2Resource = std::make_shared<DeviceApiDeviceConnectionIdDisconnect2Resource>();
	this->publish(spDeviceApiDeviceConnectionIdDisconnect2Resource);

	std::shared_ptr<DeviceApiDeviceConnectionIdEnableC2dMessagesResource> spDeviceApiDeviceConnectionIdEnableC2dMessagesResource = std::make_shared<DeviceApiDeviceConnectionIdEnableC2dMessagesResource>();
	this->publish(spDeviceApiDeviceConnectionIdEnableC2dMessagesResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdEnableMethodsResource> spDeviceApiDeviceConnectionIdEnableMethodsResource = std::make_shared<DeviceApiDeviceConnectionIdEnableMethodsResource>();
	this->publish(spDeviceApiDeviceConnectionIdEnableMethodsResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdEnableTwinResource> spDeviceApiDeviceConnectionIdEnableTwinResource = std::make_shared<DeviceApiDeviceConnectionIdEnableTwinResource>();
	this->publish(spDeviceApiDeviceConnectionIdEnableTwinResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdConnectionStatusResource> spDeviceApiDeviceConnectionIdConnectionStatusResource = std::make_shared<DeviceApiDeviceConnectionIdConnectionStatusResource>();
	this->publish(spDeviceApiDeviceConnectionIdConnectionStatusResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdTwinResource> spDeviceApiDeviceConnectionIdTwinResource = std::make_shared<DeviceApiDeviceConnectionIdTwinResource>();
	this->publish(spDeviceApiDeviceConnectionIdTwinResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdReconnectResource> spDeviceApiDeviceConnectionIdReconnectResource = std::make_shared<DeviceApiDeviceConnectionIdReconnectResource>();
	this->publish(spDeviceApiDeviceConnectionIdReconnectResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource> spDeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource = std::make_shared<DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource>();
	this->publish(spDeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdEventResource> spDeviceApiDeviceConnectionIdEventResource = std::make_shared<DeviceApiDeviceConnectionIdEventResource>();
	this->publish(spDeviceApiDeviceConnectionIdEventResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdC2dMessageResource> spDeviceApiDeviceConnectionIdC2dMessageResource = std::make_shared<DeviceApiDeviceConnectionIdC2dMessageResource>();
	this->publish(spDeviceApiDeviceConnectionIdC2dMessageResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdConnectionStatusChangeResource> spDeviceApiDeviceConnectionIdConnectionStatusChangeResource = std::make_shared<DeviceApiDeviceConnectionIdConnectionStatusChangeResource>();
	this->publish(spDeviceApiDeviceConnectionIdConnectionStatusChangeResource);

	std::shared_ptr<DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource> spDeviceApiDeviceConnectionIdTwinDesiredPropPatchResource = std::make_shared<DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource>();
	this->publish(spDeviceApiDeviceConnectionIdTwinDesiredPropPatchResource);

}

DeviceApi::~DeviceApi() {}

void DeviceApi::startService(int const& port) {
	std::shared_ptr<restbed::Settings> settings = std::make_shared<restbed::Settings>();
	settings->set_port(port);
	settings->set_root("");

	this->start(settings);
}

void DeviceApi::stopService() {
	this->stop();
}

DeviceApiDeviceConnectTransportTypeResource::DeviceApiDeviceConnectTransportTypeResource()
{
	this->set_path("/device/connect/{transportType: .*}/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectTransportTypeResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectTransportTypeResource::~DeviceApiDeviceConnectTransportTypeResource()
{
}

void DeviceApiDeviceConnectTransportTypeResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

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

			// Getting the path params
			const std::string transportType = request->get_path_parameter("transportType", "");

			// Getting the query params
			const std::string connectionString = request->get_query_parameter("connectionString", "");


			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */
			// Added 1 line in merge
			std::string ret = device_glue.Connect(transportType.c_str(), connectionString, requestBody);

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

		});
}



DeviceApiDeviceConnectionIdConnect2Resource::DeviceApiDeviceConnectionIdConnect2Resource()
{
	this->set_path("/device/{connectionId: .*}/connect2/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdConnect2Resource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdConnect2Resource::~DeviceApiDeviceConnectionIdConnect2Resource()
{
}

void DeviceApiDeviceConnectionIdConnect2Resource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceCreateFromConnectionStringTransportTypeResource::DeviceApiDeviceCreateFromConnectionStringTransportTypeResource()
{
	this->set_path("/device/createFromConnectionString/{transportType: .*}/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceCreateFromConnectionStringTransportTypeResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceCreateFromConnectionStringTransportTypeResource::~DeviceApiDeviceCreateFromConnectionStringTransportTypeResource()
{
}

void DeviceApiDeviceCreateFromConnectionStringTransportTypeResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

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

			// Getting the path params
			const std::string transportType = request->get_path_parameter("transportType", "");

			// Getting the query params
			const std::string connectionString = request->get_query_parameter("connectionString", "");


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



DeviceApiDeviceCreateFromX509TransportTypeResource::DeviceApiDeviceCreateFromX509TransportTypeResource()
{
	this->set_path("/device/createFromX509/{transportType: .*}/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceCreateFromX509TransportTypeResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceCreateFromX509TransportTypeResource::~DeviceApiDeviceCreateFromX509TransportTypeResource()
{
}

void DeviceApiDeviceCreateFromX509TransportTypeResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

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

			// Getting the path params
			const std::string transportType = request->get_path_parameter("transportType", "");



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



DeviceApiDeviceConnectionIdDestroyResource::DeviceApiDeviceConnectionIdDestroyResource()
{
	this->set_path("/device/{connectionId: .*}/destroy/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdDestroyResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdDestroyResource::~DeviceApiDeviceConnectionIdDestroyResource()
{
}

void DeviceApiDeviceConnectionIdDestroyResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdDisconnectResource::DeviceApiDeviceConnectionIdDisconnectResource()
{
	this->set_path("/device/{connectionId: .*}/disconnect/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdDisconnectResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdDisconnectResource::~DeviceApiDeviceConnectionIdDisconnectResource()
{
}

void DeviceApiDeviceConnectionIdDisconnectResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */
			# added 1 line in merge
			device_glue.Disconnect(connectionId);

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

}



DeviceApiDeviceConnectionIdDisconnect2Resource::DeviceApiDeviceConnectionIdDisconnect2Resource()
{
	this->set_path("/device/{connectionId: .*}/disconnect2/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdDisconnect2Resource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdDisconnect2Resource::~DeviceApiDeviceConnectionIdDisconnect2Resource()
{
}

void DeviceApiDeviceConnectionIdDisconnect2Resource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdEnableC2dMessagesResource::DeviceApiDeviceConnectionIdEnableC2dMessagesResource()
{
	this->set_path("/device/{connectionId: .*}/enableC2dMessages/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdEnableC2dMessagesResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdEnableC2dMessagesResource::~DeviceApiDeviceConnectionIdEnableC2dMessagesResource()
{
}

void DeviceApiDeviceConnectionIdEnableC2dMessagesResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdEnableMethodsResource::DeviceApiDeviceConnectionIdEnableMethodsResource()
{
	this->set_path("/device/{connectionId: .*}/enableMethods/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdEnableMethodsResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdEnableMethodsResource::~DeviceApiDeviceConnectionIdEnableMethodsResource()
{
}

void DeviceApiDeviceConnectionIdEnableMethodsResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */
			// Added 1 line in merge
			device_glue.EnableMethods(connectionId);

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

}



DeviceApiDeviceConnectionIdEnableTwinResource::DeviceApiDeviceConnectionIdEnableTwinResource()
{
	this->set_path("/device/{connectionId: .*}/enableTwin/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdEnableTwinResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdEnableTwinResource::~DeviceApiDeviceConnectionIdEnableTwinResource()
{
}

void DeviceApiDeviceConnectionIdEnableTwinResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdConnectionStatusResource::DeviceApiDeviceConnectionIdConnectionStatusResource()
{
	this->set_path("/device/{connectionId: .*}/connectionStatus/");
	this->set_method_handler("GET",
		std::bind(&DeviceApiDeviceConnectionIdConnectionStatusResource::GET_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdConnectionStatusResource::~DeviceApiDeviceConnectionIdConnectionStatusResource()
{
}

void DeviceApiDeviceConnectionIdConnectionStatusResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdTwinResource::DeviceApiDeviceConnectionIdTwinResource()
{
	this->set_path("/device/{connectionId: .*}/twin/");
	this->set_method_handler("GET",
		std::bind(&DeviceApiDeviceConnectionIdTwinResource::GET_method_handler, this,
			std::placeholders::_1));
	this->set_method_handler("PATCH",
		std::bind(&DeviceApiDeviceConnectionIdTwinResource::PATCH_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdTwinResource::~DeviceApiDeviceConnectionIdTwinResource()
{
}

void DeviceApiDeviceConnectionIdTwinResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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

void DeviceApiDeviceConnectionIdTwinResource::PATCH_method_handler(const std::shared_ptr<restbed::Session> session) {

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


DeviceApiDeviceConnectionIdReconnectResource::DeviceApiDeviceConnectionIdReconnectResource()
{
	this->set_path("/device/{connectionId: .*}/reconnect/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdReconnectResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdReconnectResource::~DeviceApiDeviceConnectionIdReconnectResource()
{
}

void DeviceApiDeviceConnectionIdReconnectResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");

			// Getting the query params
			const bool forceRenewPassword = request->get_query_parameter("forceRenewPassword", );


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



DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource::DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource()
{
	this->set_path("/device/{connectionId: .*}/roundtripMethodCall/{methodName: .*}/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource::~DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource()
{
}

void DeviceApiDeviceConnectionIdRoundtripMethodCallMethodNameResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

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

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");
			const std::string methodName = request->get_path_parameter("methodName", "");



			// Change the value of this variable to the appropriate response before sending the response
			int status_code = 200;

			/**
			 * Process the received information here
			 */
			// added 1 line in merge
			device_glue.RoundTripMethodCall(connectionId, methodName, requestBody);

			if (status_code == 200) {
				session->close(200, "OK", { {"Connection", "close"} });
				return;
			}

		});
}



DeviceApiDeviceConnectionIdEventResource::DeviceApiDeviceConnectionIdEventResource()
{
	this->set_path("/device/{connectionId: .*}/event/");
	this->set_method_handler("PUT",
		std::bind(&DeviceApiDeviceConnectionIdEventResource::PUT_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdEventResource::~DeviceApiDeviceConnectionIdEventResource()
{
}

void DeviceApiDeviceConnectionIdEventResource::PUT_method_handler(const std::shared_ptr<restbed::Session> session) {

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

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdC2dMessageResource::DeviceApiDeviceConnectionIdC2dMessageResource()
{
	this->set_path("/device/{connectionId: .*}/c2dMessage/");
	this->set_method_handler("GET",
		std::bind(&DeviceApiDeviceConnectionIdC2dMessageResource::GET_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdC2dMessageResource::~DeviceApiDeviceConnectionIdC2dMessageResource()
{
}

void DeviceApiDeviceConnectionIdC2dMessageResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdConnectionStatusChangeResource::DeviceApiDeviceConnectionIdConnectionStatusChangeResource()
{
	this->set_path("/device/{connectionId: .*}/connectionStatusChange/");
	this->set_method_handler("GET",
		std::bind(&DeviceApiDeviceConnectionIdConnectionStatusChangeResource::GET_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdConnectionStatusChangeResource::~DeviceApiDeviceConnectionIdConnectionStatusChangeResource()
{
}

void DeviceApiDeviceConnectionIdConnectionStatusChangeResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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



DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource::DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource()
{
	this->set_path("/device/{connectionId: .*}/twinDesiredPropPatch/");
	this->set_method_handler("GET",
		std::bind(&DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource::GET_method_handler, this,
			std::placeholders::_1));
}

DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource::~DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource()
{
}

void DeviceApiDeviceConnectionIdTwinDesiredPropPatchResource::GET_method_handler(const std::shared_ptr<restbed::Session> session) {

	const auto request = session->get_request();

			// Getting the path params
			const std::string connectionId = request->get_path_parameter("connectionId", "");



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




}
}
}
}

