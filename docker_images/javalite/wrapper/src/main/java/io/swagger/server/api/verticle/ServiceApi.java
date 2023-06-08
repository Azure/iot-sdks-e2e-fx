package io.swagger.server.api.verticle;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface ServiceApi  {
    //Service_Connect
    void serviceConnect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler);

    //Service_Disconnect
    void serviceDisconnect(String connectionId, Handler<AsyncResult<Void>> handler);

    //Service_InvokeDeviceMethod
    void serviceInvokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler);

    //Service_InvokeModuleMethod
    void serviceInvokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler);

    //Service_SendC2d
    void serviceSendC2d(String connectionId, String deviceId, EventBody eventBody, Handler<AsyncResult<Void>> handler);

}
