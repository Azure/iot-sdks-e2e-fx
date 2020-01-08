package io.swagger.server.api.verticle;

import io.swagger.server.api.MainApiException;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class NetApiImpl implements NetApi
{
    //Net_Disconnect
    @Override
    public void netDisconnect(String disconnectType, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }


    //Net_DisconnectAfterC2d
    @Override
    public void netDisconnectAfterC2d(String disconnectType, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Net_DisconnectAfterD2c
    @Override
    public void netDisconnectAfterD2c(String disconnectType, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Net_Reconnect
    @Override
    public void netReconnect(Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Net_SetDestination
    @Override
    public void netSetDestination(String ip, String transportType, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

}
