package io.swagger.server.api.verticle;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.eventbus.Message;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;

import io.swagger.server.api.MainApiException;

import java.util.List;
import java.util.Map;

public class NetApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(NetApiVerticle.class);

    final static String NET_DISCONNECT_SERVICE_ID = "Net_Disconnect";
    final static String NET_DISCONNECTAFTERC2D_SERVICE_ID = "Net_DisconnectAfterC2d";
    final static String NET_DISCONNECTAFTERD2C_SERVICE_ID = "Net_DisconnectAfterD2c";
    final static String NET_RECONNECT_SERVICE_ID = "Net_Reconnect";
    final static String NET_SETDESTINATION_SERVICE_ID = "Net_SetDestination";

    final NetApi service;

    public NetApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.NetApiImpl");
            service = (NetApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("NetApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Net_Disconnect
        vertx.eventBus().<JsonObject> consumer(NET_DISCONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Net_Disconnect";
                String disconnectTypeParam = message.body().getString("disconnectType");
                if(disconnectTypeParam == null) {
                    manageError(message, new MainApiException(400, "disconnectType is required"), serviceId);
                    return;
                }
                String disconnectType = disconnectTypeParam;
                service.netDisconnect(disconnectType, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Net_Disconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Net_Disconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Net_DisconnectAfterC2d
        vertx.eventBus().<JsonObject> consumer(NET_DISCONNECTAFTERC2D_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Net_DisconnectAfterC2d";
                String disconnectTypeParam = message.body().getString("disconnectType");
                if(disconnectTypeParam == null) {
                    manageError(message, new MainApiException(400, "disconnectType is required"), serviceId);
                    return;
                }
                String disconnectType = disconnectTypeParam;
                service.netDisconnectAfterC2d(disconnectType, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Net_DisconnectAfterC2d");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Net_DisconnectAfterC2d", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Net_DisconnectAfterD2c
        vertx.eventBus().<JsonObject> consumer(NET_DISCONNECTAFTERD2C_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Net_DisconnectAfterD2c";
                String disconnectTypeParam = message.body().getString("disconnectType");
                if(disconnectTypeParam == null) {
                    manageError(message, new MainApiException(400, "disconnectType is required"), serviceId);
                    return;
                }
                String disconnectType = disconnectTypeParam;
                service.netDisconnectAfterD2c(disconnectType, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Net_DisconnectAfterD2c");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Net_DisconnectAfterD2c", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Net_Reconnect
        vertx.eventBus().<JsonObject> consumer(NET_RECONNECT_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Net_Reconnect";
                service.netReconnect(result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Net_Reconnect");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Net_Reconnect", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Net_SetDestination
        vertx.eventBus().<JsonObject> consumer(NET_SETDESTINATION_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Net_SetDestination";
                String ipParam = message.body().getString("ip");
                if(ipParam == null) {
                    manageError(message, new MainApiException(400, "ip is required"), serviceId);
                    return;
                }
                String ip = ipParam;
                String transportTypeParam = message.body().getString("transportType");
                if(transportTypeParam == null) {
                    manageError(message, new MainApiException(400, "transportType is required"), serviceId);
                    return;
                }
                String transportType = transportTypeParam;
                service.netSetDestination(ip, transportType, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Net_SetDestination");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Net_SetDestination", e);
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
