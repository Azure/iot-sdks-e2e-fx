package io.swagger.server.api.verticle;

import io.swagger.server.api.model.LogMessage;
import io.swagger.server.api.MainApiException;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface ControlApi  {
    //Control_Cleanup
    void controlCleanup(Handler<AsyncResult<Void>> handler);

    //Control_GetCapabilities
    void controlGetCapabilities(Handler<AsyncResult<Object>> handler);

    //Control_LogMessage
    void controlLogMessage(LogMessage logMessage, Handler<AsyncResult<Void>> handler);

    //Control_SendCommand
    void controlSendCommand(String cmd, Handler<AsyncResult<Void>> handler);

    //Control_SetFlags
    void controlSetFlags(Object flags, Handler<AsyncResult<Void>> handler);

}
