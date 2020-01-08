package io.swagger.server.api.verticle;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.eventbus.Message;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;

import java.util.List;
import java.util.Map;

public class ServiceApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(ServiceApiVerticle.class);

    final static String SERVICE_CONNECT_SERVICE_ID = "Service_Connect";
    final static String SERVICE_DISCONNECT_SERVICE_ID = "Service_Disconnect";
    final static String SERVICE_INVOKEDEVICEMETHOD_SERVICE_ID = "Service_InvokeDeviceMethod";
    final static String SERVICE_INVOKEMODULEMETHOD_SERVICE_ID = "Service_InvokeModuleMethod";
    final static String SERVICE_SENDC2D_SERVICE_ID = "Service_SendC2d";

    final ServiceApi service;

    public ServiceApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.ServiceApiImpl");
            service = (ServiceApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("ServiceApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Service_Connect
        vertx.eventBus().<JsonObject> consumer(SERVICE_CONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Service_Connect";
                String connectionStringParam = message.body().getString("connectionString");
                if(connectionStringParam == null) {
                    manageError(message, new MainApiException(400, "connectionString is required"), serviceId);
                    return;
                }
                String connectionString = connectionStringParam;
                service.serviceConnect(connectionString, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Service_Connect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Service_Connect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Service_Disconnect
        vertx.eventBus().<JsonObject> consumer(SERVICE_DISCONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Service_Disconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.serviceDisconnect(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Service_Disconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Service_Disconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Service_InvokeDeviceMethod
        vertx.eventBus().<JsonObject> consumer(SERVICE_INVOKEDEVICEMETHOD_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Service_InvokeDeviceMethod";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String deviceIdParam = message.body().getString("deviceId");
                if(deviceIdParam == null) {
                    manageError(message, new MainApiException(400, "deviceId is required"), serviceId);
                    return;
                }
                String deviceId = deviceIdParam;
                JsonObject methodInvokeParametersParam = message.body().getJsonObject("methodInvokeParameters");
                if (methodInvokeParametersParam == null) {
                    manageError(message, new MainApiException(400, "methodInvokeParameters is required"), serviceId);
                    return;
                }
                MethodInvoke methodInvokeParameters = Json.mapper.readValue(methodInvokeParametersParam.encode(), MethodInvoke.class);
                service.serviceInvokeDeviceMethod(connectionId, deviceId, methodInvokeParameters, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Service_InvokeDeviceMethod");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Service_InvokeDeviceMethod", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Service_InvokeModuleMethod
        vertx.eventBus().<JsonObject> consumer(SERVICE_INVOKEMODULEMETHOD_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Service_InvokeModuleMethod";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String deviceIdParam = message.body().getString("deviceId");
                if(deviceIdParam == null) {
                    manageError(message, new MainApiException(400, "deviceId is required"), serviceId);
                    return;
                }
                String deviceId = deviceIdParam;
                String moduleIdParam = message.body().getString("moduleId");
                if(moduleIdParam == null) {
                    manageError(message, new MainApiException(400, "moduleId is required"), serviceId);
                    return;
                }
                String moduleId = moduleIdParam;
                JsonObject methodInvokeParametersParam = message.body().getJsonObject("methodInvokeParameters");
                if (methodInvokeParametersParam == null) {
                    manageError(message, new MainApiException(400, "methodInvokeParameters is required"), serviceId);
                    return;
                }
                MethodInvoke methodInvokeParameters = Json.mapper.readValue(methodInvokeParametersParam.encode(), MethodInvoke.class);
                service.serviceInvokeModuleMethod(connectionId, deviceId, moduleId, methodInvokeParameters, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Service_InvokeModuleMethod");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Service_InvokeModuleMethod", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Service_SendC2d
        vertx.eventBus().<JsonObject> consumer(SERVICE_SENDC2D_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Service_SendC2d";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String deviceIdParam = message.body().getString("deviceId");
                if(deviceIdParam == null) {
                    manageError(message, new MainApiException(400, "deviceId is required"), serviceId);
                    return;
                }
                String deviceId = deviceIdParam;
                JsonObject eventBodyParam = message.body().getJsonObject("eventBody");
                if (eventBodyParam == null) {
                    manageError(message, new MainApiException(400, "eventBody is required"), serviceId);
                    return;
                }
                EventBody eventBody = Json.mapper.readValue(eventBodyParam.encode(), EventBody.class);
                service.serviceSendC2d(connectionId, deviceId, eventBody, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Service_SendC2d");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Service_SendC2d", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

    }

    private void manageError(Message<JsonObject> message, Throwable cause, String serviceName) {
        int code = MainApiException.INTERNAL_SERVER_ERROR.getStatusCode();
        String statusMessage = MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage();
        if (cause instanceof MainApiException) {
            code = ((MainApiException)cause).getStatusCode();
            statusMessage = ((MainApiException)cause).getStatusMessage();
        } else {
            logUnexpectedError(serviceName, cause);
        }

        message.fail(code, statusMessage);
    }

    private void logUnexpectedError(String serviceName, Throwable cause) {
        LOGGER.error("Unexpected error in "+ serviceName, cause);
    }
}
