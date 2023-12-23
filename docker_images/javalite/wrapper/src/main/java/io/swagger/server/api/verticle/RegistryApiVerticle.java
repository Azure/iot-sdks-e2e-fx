package io.swagger.server.api.verticle;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.eventbus.Message;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.Twin;

import java.util.List;
import java.util.Map;

public class RegistryApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(RegistryApiVerticle.class);

    final static String REGISTRY_CONNECT_SERVICE_ID = "Registry_Connect";
    final static String REGISTRY_DISCONNECT_SERVICE_ID = "Registry_Disconnect";
    final static String REGISTRY_GETDEVICETWIN_SERVICE_ID = "Registry_GetDeviceTwin";
    final static String REGISTRY_GETMODULETWIN_SERVICE_ID = "Registry_GetModuleTwin";
    final static String REGISTRY_PATCHDEVICETWIN_SERVICE_ID = "Registry_PatchDeviceTwin";
    final static String REGISTRY_PATCHMODULETWIN_SERVICE_ID = "Registry_PatchModuleTwin";

    final RegistryApi service;

    public RegistryApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.RegistryApiImpl");
            service = (RegistryApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("RegistryApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Registry_Connect
        vertx.eventBus().<JsonObject> consumer(REGISTRY_CONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_Connect";
                String connectionStringParam = message.body().getString("connectionString");
                if(connectionStringParam == null) {
                    manageError(message, new MainApiException(400, "connectionString is required"), serviceId);
                    return;
                }
                String connectionString = connectionStringParam;
                service.registryConnect(connectionString, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_Connect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_Connect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Registry_Disconnect
        vertx.eventBus().<JsonObject> consumer(REGISTRY_DISCONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_Disconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.registryDisconnect(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_Disconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_Disconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Registry_GetDeviceTwin
        vertx.eventBus().<JsonObject> consumer(REGISTRY_GETDEVICETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_GetDeviceTwin";
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
                service.registryGetDeviceTwin(connectionId, deviceId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_GetDeviceTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_GetDeviceTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Registry_GetModuleTwin
        vertx.eventBus().<JsonObject> consumer(REGISTRY_GETMODULETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_GetModuleTwin";
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
                service.registryGetModuleTwin(connectionId, deviceId, moduleId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_GetModuleTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_GetModuleTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Registry_PatchDeviceTwin
        vertx.eventBus().<JsonObject> consumer(REGISTRY_PATCHDEVICETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_PatchDeviceTwin";
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
                JsonObject twinParam = message.body().getJsonObject("twin");
                if (twinParam == null) {
                    manageError(message, new MainApiException(400, "twin is required"), serviceId);
                    return;
                }
                Twin twin = Json.mapper.readValue(twinParam.encode(), Twin.class);
                service.registryPatchDeviceTwin(connectionId, deviceId, twin, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_PatchDeviceTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_PatchDeviceTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Registry_PatchModuleTwin
        vertx.eventBus().<JsonObject> consumer(REGISTRY_PATCHMODULETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Registry_PatchModuleTwin";
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
                JsonObject twinParam = message.body().getJsonObject("twin");
                if (twinParam == null) {
                    manageError(message, new MainApiException(400, "twin is required"), serviceId);
                    return;
                }
                Twin twin = Json.mapper.readValue(twinParam.encode(), Twin.class);
                service.registryPatchModuleTwin(connectionId, deviceId, moduleId, twin, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Registry_PatchModuleTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Registry_PatchModuleTwin", e);
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
