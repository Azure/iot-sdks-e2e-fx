package io.swagger.server.api.verticle;

// Added 1 line in merge
import glue.ControlGlue;

import io.swagger.server.api.MainApiException;

import io.swagger.server.api.model.LogMessage;
import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class ControlApiImpl implements ControlApi
{
    // Added 1 line in merge
    private ControlGlue _ControlGlue= new ControlGlue();

    //Control_Cleanup
    @Override
    public void controlCleanup(Handler<AsyncResult<Void>> handler)
    {
        this._ControlGlue.Cleanup(handler);
    }

    //Control_GetCapabilities
    @Override
    public void controlGetCapabilities(Handler<AsyncResult<Object>> handler)
    {
        _ControlGlue.getCapabilities(handler);
    }

    //Control_LogMessage
    @Override
    public void controlLogMessage(LogMessage logMessage, Handler<AsyncResult<Void>> handler)
    {
        this._ControlGlue.outputMessage(logMessage, handler);
    }

    //Control_SendCommand
    @Override
    public void controlSendCommand(String cmd, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Control_SetFlags
    @Override
    public void controlSetFlags(Object flags, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

}
