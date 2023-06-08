package io.swagger.server.api.verticle;

import io.swagger.server.api.MainApiException;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface NetApi  {
    //Net_Disconnect
    void netDisconnect(String disconnectType, Handler<AsyncResult<Void>> handler);

    //Net_DisconnectAfterC2d
    void netDisconnectAfterC2d(String disconnectType, Handler<AsyncResult<Void>> handler);

    //Net_DisconnectAfterD2c
    void netDisconnectAfterD2c(String disconnectType, Handler<AsyncResult<Void>> handler);

    //Net_Reconnect
    void netReconnect(Handler<AsyncResult<Void>> handler);

    //Net_SetDestination
    void netSetDestination(String ip, String transportType, Handler<AsyncResult<Void>> handler);

}
