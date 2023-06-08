package io.swagger.server.api.verticle;

import io.swagger.server.api.model.*;
import io.swagger.server.api.MainApiException;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class DeviceApiImpl implements DeviceApi
{
    //Device_Connect
    @Override
    public void deviceConnect(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_Connect2
    @Override
    public void deviceConnect2(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_CreateFromConnectionString
    @Override
    public void deviceCreateFromConnectionString(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_CreateFromX509
    @Override
    public void deviceCreateFromX509(String transportType, Object x509, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_Destroy
    @Override
    public void deviceDestroy(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_Disconnect
    @Override
    public void deviceDisconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_Disconnect2
    @Override
    public void deviceDisconnect2(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_EnableC2dMessages
    @Override
    public void deviceEnableC2dMessages(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_EnableMethods
    @Override
    public void deviceEnableMethods(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_EnableTwin
    @Override
    public void deviceEnableTwin(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_GetConnectionStatus
    @Override
    public void deviceGetConnectionStatus(String connectionId, Handler<AsyncResult<String>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_GetTwin
    @Override
    public void deviceGetTwin(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_PatchTwin
    @Override
    public void devicePatchTwin(String connectionId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_Reconnect
    @Override
    public void deviceReconnect(String connectionId, Boolean forceRenewPassword, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_WaitForMethodAndReturnResponse
    @Override
    public void deviceWaitForMethodAndReturnResponse(String connectionId, String methodName, MethodRequestAndResponse requestAndResponse, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_SendEvent
    @Override
    public void deviceSendEvent(String connectionId, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_WaitForC2dMessage
    @Override
    public void deviceWaitForC2dMessage(String connectionId, Handler<AsyncResult<EventBody>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_WaitForConnectionStatusChange
    @Override
    public void deviceWaitForConnectionStatusChange(String connectionId, Handler<AsyncResult<String>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Device_WaitForDesiredPropertiesPatch
    @Override
    public void deviceWaitForDesiredPropertiesPatch(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }


}
