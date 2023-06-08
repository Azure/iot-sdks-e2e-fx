package io.swagger.server.api.verticle;

import io.vertx.core.AbstractVerticle;
import io.vertx.core.eventbus.Message;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonArray;
import io.vertx.core.json.JsonObject;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;

import io.swagger.server.api.model.LogMessage;
import io.swagger.server.api.MainApiException;

import java.util.List;
import java.util.Map;

public class ControlApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(ControlApiVerticle.class);

    final static String CONTROL_CLEANUP_SERVICE_ID = "Control_Cleanup";
    final static String CONTROL_GETCAPABILITIES_SERVICE_ID = "Control_GetCapabilities";
    final static String CONTROL_LOGMESSAGE_SERVICE_ID = "Control_LogMessage";
    final static String CONTROL_SENDCOMMAND_SERVICE_ID = "Control_SendCommand";
    final static String CONTROL_SETFLAGS_SERVICE_ID = "Control_SetFlags";

    final ControlApi service;

    public ControlApiVerticle() {
        try {
            Class serviceImplClass = getClass().getClassLoader().loadClass("io.swagger.server.api.verticle.ControlApiImpl");
            service = (ControlApi)serviceImplClass.newInstance();
        } catch (Exception e) {
            logUnexpectedError("ControlApiVerticle constructor", e);
            throw new RuntimeException(e);
        }
    }

    @Override
    public void start() throws Exception {

        //Consumer for Control_Cleanup
        vertx.eventBus().<JsonObject> consumer(CONTROL_CLEANUP_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Control_Cleanup";
                service.controlCleanup(result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Control_Cleanup");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Control_Cleanup", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Control_GetCapabilities
        vertx.eventBus().<JsonObject> consumer(CONTROL_GETCAPABILITIES_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Control_GetCapabilities";
                service.controlGetCapabilities(result -> {
                    if (result.succeeded())
                        message.reply(new JsonObject(Json.encode(result.result())).encodePrettily());
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Control_GetCapabilities");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Control_GetCapabilities", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Control_LogMessage
        vertx.eventBus().<JsonObject> consumer(CONTROL_LOGMESSAGE_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Control_LogMessage";
                JsonObject logMessageParam = message.body().getJsonObject("logMessage");
                if (logMessageParam == null) {
                    manageError(message, new MainApiException(400, "logMessage is required"), serviceId);
                    return;
                }
                LogMessage logMessage = Json.mapper.readValue(logMessageParam.encode(), LogMessage.class);
                service.controlLogMessage(logMessage, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Control_LogMessage");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Control_LogMessage", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Control_SendCommand
        vertx.eventBus().<JsonObject> consumer(CONTROL_SENDCOMMAND_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Control_SendCommand";
                String cmdParam = message.body().getString("cmd");
                if(cmdParam == null) {
                    manageError(message, new MainApiException(400, "cmd is required"), serviceId);
                    return;
                }
                String cmd = cmdParam;
                service.controlSendCommand(cmd, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Control_SendCommand");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Control_SendCommand", e);
                message.fail(MainApiException.INTERNAL_SERVER_ERROR.getStatusCode(), MainApiException.INTERNAL_SERVER_ERROR.getStatusMessage());
            }
        });

        //Consumer for Control_SetFlags
        vertx.eventBus().<JsonObject> consumer(CONTROL_SETFLAGS_SERVICE_ID).handler(message -> {
            try {
                // Workaround for #allParams section clearing the vendorExtensions map
                String serviceId = "Control_SetFlags";
                String flagsParam = message.body().getString("flags");
                if(flagsParam == null) {
                    manageError(message, new MainApiException(400, "flags is required"), serviceId);
                    return;
                }
                Object flags = Json.mapper.readValue(flagsParam, Object.class);
                service.controlSetFlags(flags, result -> {
                    if (result.succeeded())
                        message.reply(null);
                    else {
                        Throwable cause = result.cause();
                        manageError(message, cause, "Control_SetFlags");
                    }
                });
            } catch (Exception e) {
                logUnexpectedError("Control_SetFlags", e);
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
