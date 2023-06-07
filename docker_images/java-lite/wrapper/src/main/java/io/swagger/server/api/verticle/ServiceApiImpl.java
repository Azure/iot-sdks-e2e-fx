package io.swagger.server.api.verticle;

// Added 1 line in merge
import glue.ServiceGlue;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.MainApiException;

import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.model.MethodInvoke;
import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class ServiceApiImpl implements ServiceApi
{
    // Added 1 line in merge
    public static ServiceGlue _serviceGlue = new ServiceGlue();

    //Service_Connect
    @Override
    public void serviceConnect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler)
    {
        this._serviceGlue.connect(connectionString, handler);
    }

    //Service_Disconnect
    @Override
    public void serviceDisconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._serviceGlue.disconnect(connectionId, handler);
    }

    //Service_InvokeDeviceMethod
    @Override
    public void serviceInvokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        this._serviceGlue.invokeDeviceMethod(connectionId, deviceId, methodInvokeParameters, handler);
    }

    //Service_InvokeModuleMethod
    @Override
    public void serviceInvokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        this._serviceGlue.invokeModuleMethod(connectionId, deviceId, moduleId, methodInvokeParameters, handler);
    }

    //Service_SendC2d
    @Override
    public void serviceSendC2d(String connectionId, String deviceId, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

}
