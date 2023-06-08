package io.swagger.server.api.verticle;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.eventbus.Message;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;

import io.swagger.server.api.model.Certificate;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;

import java.util.List;
import java.util.Map;

public class ModuleApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(ModuleApiVerticle.class);

    final static String MODULE_CONNECT_SERVICE_ID = "Module_Connect";
    final static String MODULE_CONNECT2_SERVICE_ID = "Module_Connect2";
    final static String MODULE_CONNECTFROMENVIRONMENT_SERVICE_ID = "Module_ConnectFromEnvironment";
    final static String MODULE_CREATEFROMCONNECTIONSTRING_SERVICE_ID = "Module_CreateFromConnectionString";
    final static String MODULE_CREATEFROMENVIRONMENT_SERVICE_ID = "Module_CreateFromEnvironment";
    final static String MODULE_CREATEFROMX509_SERVICE_ID = "Module_CreateFromX509";
    final static String MODULE_DESTROY_SERVICE_ID = "Module_Destroy";
    final static String MODULE_DISCONNECT_SERVICE_ID = "Module_Disconnect";
    final static String MODULE_DISCONNECT2_SERVICE_ID = "Module_Disconnect2";
    final static String MODULE_ENABLEINPUTMESSAGES_SERVICE_ID = "Module_EnableInputMessages";
    final static String MODULE_ENABLEMETHODS_SERVICE_ID = "Module_EnableMethods";
    final static String MODULE_ENABLETWIN_SERVICE_ID = "Module_EnableTwin";
    final static String MODULE_GETCONNECTIONSTATUS_SERVICE_ID = "Module_GetConnectionStatus";
    final static String MODULE_GETTWIN_SERVICE_ID = "Module_GetTwin";
    final static String MODULE_INVOKEDEVICEMETHOD_SERVICE_ID = "Module_InvokeDeviceMethod";
    final static String MODULE_INVOKEMODULEMETHOD_SERVICE_ID = "Module_InvokeModuleMethod";
    final static String MODULE_PATCHTWIN_SERVICE_ID = "Module_PatchTwin";
    final static String MODULE_RECONNECT_SERVICE_ID = "Module_Reconnect";
    final static String MODULE_SENDEVENT_SERVICE_ID = "Module_SendEvent";
    final static String MODULE_SENDOUTPUTEVENT_SERVICE_ID = "Module_SendOutputEvent";
    final static String MODULE_WAITFORCONNECTIONSTATUSCHANGE_SERVICE_ID = "Module_WaitForConnectionStatusChange";
    final static String MODULE_WAITFORDESIREDPROPERTIESPATCH_SERVICE_ID = "Module_WaitForDesiredPropertiesPatch";
    final static String MODULE_WAITFORINPUTMESSAGE_SERVICE_ID = "Module_WaitForInputMessage";
    final static String MODULE_WAITFORMETHODANDRETURNRESPONSE_SERVICE_ID = "Module_WaitForMethodAndReturnResponse";

    final ModuleApi service;

    public ModuleApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.ModuleApiImpl");
            service = (ModuleApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("ModuleApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Module_Connect
        vertx.eventBus().<JsonObject> consumer(MODULE_CONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Connect";
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                String connectionStringParam = message.body().getString("connectionString");
                if(connectionStringParam == null) {
                    manageError(message, new MainApiException(400, "connectionString is required"), serviceId);
                    return;
                }
                String connectionString = connectionStringParam;
                JsonObject caCertificateParam = message.body().getJsonObject("caCertificate");
                if (caCertificateParam == null) {
                    manageError(message, new MainApiException(400, "caCertificate is required"), serviceId);
                    return;
                }
                Certificate caCertificate = Json.mapper.readValue(caCertificateParam.encode(), Certificate.class);
                service.moduleConnect(transportType, connectionString, caCertificate, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Connect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Connect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_Connect2
        vertx.eventBus().<JsonObject> consumer(MODULE_CONNECT2_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Connect2";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleConnect2(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Connect2");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Connect2", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_ConnectFromEnvironment
        vertx.eventBus().<JsonObject> consumer(MODULE_CONNECTFROMENVIRONMENT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_ConnectFromEnvironment";
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                service.moduleConnectFromEnvironment(transportType, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_ConnectFromEnvironment");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_ConnectFromEnvironment", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_CreateFromConnectionString
        vertx.eventBus().<JsonObject> consumer(MODULE_CREATEFROMCONNECTIONSTRING_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_CreateFromConnectionString";
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                String connectionStringParam = message.body().getString("connectionString");
                if(connectionStringParam == null) {
                    manageError(message, new MainApiException(400, "connectionString is required"), serviceId);
                    return;
                }
                String connectionString = connectionStringParam;
                JsonObject caCertificateParam = message.body().getJsonObject("caCertificate");
                if (caCertificateParam == null) {
                    manageError(message, new MainApiException(400, "caCertificate is required"), serviceId);
                    return;
                }
                Certificate caCertificate = Json.mapper.readValue(caCertificateParam.encode(), Certificate.class);
                service.moduleCreateFromConnectionString(transportType, connectionString, caCertificate, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_CreateFromConnectionString");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_CreateFromConnectionString", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_CreateFromEnvironment
        vertx.eventBus().<JsonObject> consumer(MODULE_CREATEFROMENVIRONMENT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_CreateFromEnvironment";
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                service.moduleCreateFromEnvironment(transportType, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_CreateFromEnvironment");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_CreateFromEnvironment", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_CreateFromX509
        vertx.eventBus().<JsonObject> consumer(MODULE_CREATEFROMX509_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_CreateFromX509";
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                String x509Param = message.body().getString("X509");
                if(x509Param == null) {
                    manageError(message, new MainApiException(400, "X509 is required"), serviceId);
                    return;
                }
                Object x509 = Json.mapper.readValue(x509Param, Object.class);
                service.moduleCreateFromX509(transportType, x509, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_CreateFromX509");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_CreateFromX509", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_Destroy
        vertx.eventBus().<JsonObject> consumer(MODULE_DESTROY_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Destroy";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleDestroy(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Destroy");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Destroy", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_Disconnect
        vertx.eventBus().<JsonObject> consumer(MODULE_DISCONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Disconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleDisconnect(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Disconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Disconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_Disconnect2
        vertx.eventBus().<JsonObject> consumer(MODULE_DISCONNECT2_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Disconnect2";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleDisconnect2(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Disconnect2");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Disconnect2", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_EnableInputMessages
        vertx.eventBus().<JsonObject> consumer(MODULE_ENABLEINPUTMESSAGES_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_EnableInputMessages";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleEnableInputMessages(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_EnableInputMessages");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_EnableInputMessages", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_EnableMethods
        vertx.eventBus().<JsonObject> consumer(MODULE_ENABLEMETHODS_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_EnableMethods";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleEnableMethods(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_EnableMethods");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_EnableMethods", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_EnableTwin
        vertx.eventBus().<JsonObject> consumer(MODULE_ENABLETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_EnableTwin";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleEnableTwin(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_EnableTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_EnableTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_GetConnectionStatus
        vertx.eventBus().<JsonObject> consumer(MODULE_GETCONNECTIONSTATUS_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_GetConnectionStatus";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleGetConnectionStatus(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_GetConnectionStatus");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_GetConnectionStatus", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_GetTwin
        vertx.eventBus().<JsonObject> consumer(MODULE_GETTWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_GetTwin";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleGetTwin(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_GetTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_GetTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_InvokeDeviceMethod
        vertx.eventBus().<JsonObject> consumer(MODULE_INVOKEDEVICEMETHOD_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_InvokeDeviceMethod";
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
                service.moduleInvokeDeviceMethod(connectionId, deviceId, methodInvokeParameters, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_InvokeDeviceMethod");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_InvokeDeviceMethod", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_InvokeModuleMethod
        vertx.eventBus().<JsonObject> consumer(MODULE_INVOKEMODULEMETHOD_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_InvokeModuleMethod";
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
                service.moduleInvokeModuleMethod(connectionId, deviceId, moduleId, methodInvokeParameters, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_InvokeModuleMethod");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_InvokeModuleMethod", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_PatchTwin
        vertx.eventBus().<JsonObject> consumer(MODULE_PATCHTWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_PatchTwin";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                JsonObject twinParam = message.body().getJsonObject("twin");
                if (twinParam == null) {
                    manageError(message, new MainApiException(400, "twin is required"), serviceId);
                    return;
                }
                Twin twin = Json.mapper.readValue(twinParam.encode(), Twin.class);
                service.modulePatchTwin(connectionId, twin, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_PatchTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_PatchTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_Reconnect
        vertx.eventBus().<JsonObject> consumer(MODULE_RECONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_Reconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String forceRenewPasswordParam = message.body().getString("forceRenewPassword");
                Boolean forceRenewPassword = (forceRenewPasswordParam == null) ? null : Json.mapper.readValue(forceRenewPasswordParam, Boolean.class);
                service.moduleReconnect(connectionId, forceRenewPassword, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_Reconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_Reconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_SendEvent
        vertx.eventBus().<JsonObject> consumer(MODULE_SENDEVENT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_SendEvent";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                JsonObject eventBodyParam = message.body().getJsonObject("eventBody");
                if (eventBodyParam == null) {
                    manageError(message, new MainApiException(400, "eventBody is required"), serviceId);
                    return;
                }
                EventBody eventBody = Json.mapper.readValue(eventBodyParam.encode(), EventBody.class);
                service.moduleSendEvent(connectionId, eventBody, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_SendEvent");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_SendEvent", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_SendOutputEvent
        vertx.eventBus().<JsonObject> consumer(MODULE_SENDOUTPUTEVENT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_SendOutputEvent";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String outputNameParam = message.body().getString("outputName");
                if(outputNameParam == null) {
                    manageError(message, new MainApiException(400, "outputName is required"), serviceId);
                    return;
                }
                String outputName = outputNameParam;
                JsonObject eventBodyParam = message.body().getJsonObject("eventBody");
                if (eventBodyParam == null) {
                    manageError(message, new MainApiException(400, "eventBody is required"), serviceId);
                    return;
                }
                EventBody eventBody = Json.mapper.readValue(eventBodyParam.encode(), EventBody.class);
                service.moduleSendOutputEvent(connectionId, outputName, eventBody, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_SendOutputEvent");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_SendOutputEvent", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_WaitForConnectionStatusChange
        vertx.eventBus().<JsonObject> consumer(MODULE_WAITFORCONNECTIONSTATUSCHANGE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_WaitForConnectionStatusChange";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleWaitForConnectionStatusChange(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_WaitForConnectionStatusChange");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_WaitForConnectionStatusChange", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_WaitForDesiredPropertiesPatch
        vertx.eventBus().<JsonObject> consumer(MODULE_WAITFORDESIREDPROPERTIESPATCH_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_WaitForDesiredPropertiesPatch";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.moduleWaitForDesiredPropertiesPatch(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_WaitForDesiredPropertiesPatch");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_WaitForDesiredPropertiesPatch", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_WaitForInputMessage
        vertx.eventBus().<JsonObject> consumer(MODULE_WAITFORINPUTMESSAGE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_WaitForInputMessage";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String inputNameParam = message.body().getString("inputName");
                if(inputNameParam == null) {
                    manageError(message, new MainApiException(400, "inputName is required"), serviceId);
                    return;
                }
                String inputName = inputNameParam;
                service.moduleWaitForInputMessage(connectionId, inputName, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_WaitForInputMessage");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_WaitForInputMessage", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Module_WaitForMethodAndReturnResponse
        vertx.eventBus().<JsonObject> consumer(MODULE_WAITFORMETHODANDRETURNRESPONSE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Module_WaitForMethodAndReturnResponse";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String methodNameParam = message.body().getString("methodName");
                if(methodNameParam == null) {
                    manageError(message, new MainApiException(400, "methodName is required"), serviceId);
                    return;
                }
                String methodName = methodNameParam;
                JsonObject requestAndResponseParam = message.body().getJsonObject("requestAndResponse");
                if (requestAndResponseParam == null) {
                    manageError(message, new MainApiException(400, "requestAndResponse is required"), serviceId);
                    return;
                }
                MethodRequestAndResponse requestAndResponse = Json.mapper.readValue(requestAndResponseParam.encode(), MethodRequestAndResponse.class);
                service.moduleWaitForMethodAndReturnResponse(connectionId, methodName, requestAndResponse, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Module_WaitForMethodAndReturnResponse");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Module_WaitForMethodAndReturnResponse", e);
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
