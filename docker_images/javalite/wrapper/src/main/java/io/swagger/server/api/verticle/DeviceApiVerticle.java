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
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;

import java.util.List;
import java.util.Map;

public class DeviceApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(DeviceApiVerticle.class);

    final static String DEVICE_CONNECT_SERVICE_ID = "Device_Connect";
    final static String DEVICE_CONNECT2_SERVICE_ID = "Device_Connect2";
    final static String DEVICE_CREATEFROMCONNECTIONSTRING_SERVICE_ID = "Device_CreateFromConnectionString";
    final static String DEVICE_CREATEFROMX509_SERVICE_ID = "Device_CreateFromX509";
    final static String DEVICE_DESTROY_SERVICE_ID = "Device_Destroy";
    final static String DEVICE_DISCONNECT_SERVICE_ID = "Device_Disconnect";
    final static String DEVICE_DISCONNECT2_SERVICE_ID = "Device_Disconnect2";
    final static String DEVICE_ENABLEC2DMESSAGES_SERVICE_ID = "Device_EnableC2dMessages";
    final static String DEVICE_ENABLEMETHODS_SERVICE_ID = "Device_EnableMethods";
    final static String DEVICE_ENABLETWIN_SERVICE_ID = "Device_EnableTwin";
    final static String DEVICE_GETCONNECTIONSTATUS_SERVICE_ID = "Device_GetConnectionStatus";
    final static String DEVICE_GETTWIN_SERVICE_ID = "Device_GetTwin";
    final static String DEVICE_PATCHTWIN_SERVICE_ID = "Device_PatchTwin";
    final static String DEVICE_RECONNECT_SERVICE_ID = "Device_Reconnect";
    final static String DEVICE_SENDEVENT_SERVICE_ID = "Device_SendEvent";
    final static String DEVICE_WAITFORC2DMESSAGE_SERVICE_ID = "Device_WaitForC2dMessage";
    final static String DEVICE_WAITFORCONNECTIONSTATUSCHANGE_SERVICE_ID = "Device_WaitForConnectionStatusChange";
    final static String DEVICE_WAITFORDESIREDPROPERTIESPATCH_SERVICE_ID = "Device_WaitForDesiredPropertiesPatch";
    final static String DEVICE_WAITFORMETHODANDRETURNRESPONSE_SERVICE_ID = "Device_WaitForMethodAndReturnResponse";

    final DeviceApi service;

    public DeviceApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.DeviceApiImpl");
            service = (DeviceApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("DeviceApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Device_Connect
        vertx.eventBus().<JsonObject> consumer(DEVICE_CONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Connect";
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
                service.deviceConnect(transportType, connectionString, caCertificate, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Connect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Connect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_Connect2
        vertx.eventBus().<JsonObject> consumer(DEVICE_CONNECT2_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Connect2";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceConnect2(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Connect2");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Connect2", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_CreateFromConnectionString
        vertx.eventBus().<JsonObject> consumer(DEVICE_CREATEFROMCONNECTIONSTRING_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_CreateFromConnectionString";
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
                service.deviceCreateFromConnectionString(transportType, connectionString, caCertificate, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_CreateFromConnectionString");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_CreateFromConnectionString", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_CreateFromX509
        vertx.eventBus().<JsonObject> consumer(DEVICE_CREATEFROMX509_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_CreateFromX509";
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
                service.deviceCreateFromX509(transportType, x509, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_CreateFromX509");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_CreateFromX509", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_Destroy
        vertx.eventBus().<JsonObject> consumer(DEVICE_DESTROY_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Destroy";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceDestroy(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Destroy");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Destroy", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_Disconnect
        vertx.eventBus().<JsonObject> consumer(DEVICE_DISCONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Disconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceDisconnect(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Disconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Disconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_Disconnect2
        vertx.eventBus().<JsonObject> consumer(DEVICE_DISCONNECT2_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Disconnect2";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceDisconnect2(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Disconnect2");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Disconnect2", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_EnableC2dMessages
        vertx.eventBus().<JsonObject> consumer(DEVICE_ENABLEC2DMESSAGES_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_EnableC2dMessages";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceEnableC2dMessages(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_EnableC2dMessages");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_EnableC2dMessages", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_EnableMethods
        vertx.eventBus().<JsonObject> consumer(DEVICE_ENABLEMETHODS_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_EnableMethods";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceEnableMethods(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_EnableMethods");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_EnableMethods", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_EnableTwin
        vertx.eventBus().<JsonObject> consumer(DEVICE_ENABLETWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_EnableTwin";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceEnableTwin(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_EnableTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_EnableTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_GetConnectionStatus
        vertx.eventBus().<JsonObject> consumer(DEVICE_GETCONNECTIONSTATUS_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_GetConnectionStatus";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceGetConnectionStatus(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_GetConnectionStatus");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_GetConnectionStatus", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_GetTwin
        vertx.eventBus().<JsonObject> consumer(DEVICE_GETTWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_GetTwin";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceGetTwin(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_GetTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_GetTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_PatchTwin
        vertx.eventBus().<JsonObject> consumer(DEVICE_PATCHTWIN_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_PatchTwin";
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
                service.devicePatchTwin(connectionId, twin, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_PatchTwin");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_PatchTwin", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_Reconnect
        vertx.eventBus().<JsonObject> consumer(DEVICE_RECONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_Reconnect";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                String forceRenewPasswordParam = message.body().getString("forceRenewPassword");
                Boolean forceRenewPassword = (forceRenewPasswordParam == null) ? null : Json.mapper.readValue(forceRenewPasswordParam, Boolean.class);
                service.deviceReconnect(connectionId, forceRenewPassword, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_Reconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_Reconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_SendEvent
        vertx.eventBus().<JsonObject> consumer(DEVICE_SENDEVENT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_SendEvent";
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
                service.deviceSendEvent(connectionId, eventBody, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_SendEvent");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_SendEvent", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_WaitForC2dMessage
        vertx.eventBus().<JsonObject> consumer(DEVICE_WAITFORC2DMESSAGE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_WaitForC2dMessage";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceWaitForC2dMessage(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_WaitForC2dMessage");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_WaitForC2dMessage", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_WaitForConnectionStatusChange
        vertx.eventBus().<JsonObject> consumer(DEVICE_WAITFORCONNECTIONSTATUSCHANGE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_WaitForConnectionStatusChange";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceWaitForConnectionStatusChange(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_WaitForConnectionStatusChange");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_WaitForConnectionStatusChange", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_WaitForDesiredPropertiesPatch
        vertx.eventBus().<JsonObject> consumer(DEVICE_WAITFORDESIREDPROPERTIESPATCH_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_WaitForDesiredPropertiesPatch";
                String connectionIdParam = message.body().getString("connectionId");
                if(connectionIdParam == null) {
                    manageError(message, new MainApiException(400, "connectionId is required"), serviceId);
                    return;
                }
                String connectionId = connectionIdParam;
                service.deviceWaitForDesiredPropertiesPatch(connectionId, result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_WaitForDesiredPropertiesPatch");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_WaitForDesiredPropertiesPatch", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Device_WaitForMethodAndReturnResponse
        vertx.eventBus().<JsonObject> consumer(DEVICE_WAITFORMETHODANDRETURNRESPONSE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Device_WaitForMethodAndReturnResponse";
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
                service.deviceWaitForMethodAndReturnResponse(connectionId, methodName, requestAndResponse, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Device_WaitForMethodAndReturnResponse");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Device_WaitForMethodAndReturnResponse", e);
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
