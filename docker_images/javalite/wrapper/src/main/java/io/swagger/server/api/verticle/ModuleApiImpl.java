package io.swagger.server.api.verticle;


// Added 1 lines in merge
import glue.ModuleGlue;

import io.swagger.server.api.model.*;
import io.swagger.server.api.MainApiException;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class ModuleApiImpl implements ModuleApi
{
    // Added 1 line in merge
    public static ModuleGlue _moduleGlue = new ModuleGlue();

    //Module_Connect
    @Override
    public void moduleConnect(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler)
    {
        this._moduleGlue.connect(transportType, connectionString, caCertificate, handler);
    }

    //Module_Connect2
    @Override
    public void moduleConnect2(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_ConnectFromEnvironment
    @Override
    public void moduleConnectFromEnvironment(String transportType, Handler<AsyncResult<ConnectResponse>> handler)
    {
        this._moduleGlue.connectFromEnvironment(transportType, handler);
    }

    //Module_CreateFromConnectionString
    @Override
    public void moduleCreateFromConnectionString(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_CreateFromEnvironment
    @Override
    public void moduleCreateFromEnvironment(String transportType, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_CreateFromX509
    @Override
    public void moduleCreateFromX509(String transportType, Object x509, Handler<AsyncResult<ConnectResponse>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_Destroy
    @Override
    public void moduleDestroy(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_Disconnect
    @Override
    public void moduleDisconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.disconnect(connectionId, handler);
    }

    //Module_Disconnect2
    @Override
    public void moduleDisconnect2(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_EnableInputMessages
    @Override
    public void moduleEnableInputMessages(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.enableInputMessages(connectionId, handler);
    }

    //Module_EnableMethods
    @Override
    public void moduleEnableMethods(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.enableMethods(connectionId, handler);
    }

    //Module_EnableTwin
    @Override
    public void moduleEnableTwin(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.enableTwin(connectionId, handler);
    }

    //Module_GetConnectionStatus
    @Override
    public void moduleGetConnectionStatus(String connectionId, Handler<AsyncResult<String>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_GetTwin
    @Override
    public void moduleGetTwin(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        this._moduleGlue.getTwin(connectionId, handler);
    }

    //Module_InvokeDeviceMethod
    @Override
    public void moduleInvokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        this._moduleGlue.invokeDeviceMethod(connectionId, deviceId, methodInvokeParameters, handler);
    }

    //Module_InvokeModuleMethod
    @Override
    public void moduleInvokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        this._moduleGlue.invokeModuleMethod(connectionId, deviceId, moduleId, methodInvokeParameters, handler);
    }

    //Module_PatchTwin
    @Override
    public void modulePatchTwin(String connectionId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.sendTwinPatch(connectionId, twin, handler);
    }

    //Module_Reconnect
    @Override
    public void moduleReconnect(String connectionId, Boolean forceRenewPassword, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_SendEvent
    @Override
    public void moduleSendEvent(String connectionId, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.sendEvent(connectionId, eventBody, handler);
    }

    //Module_SendOutputEvent
    @Override
    public void moduleSendOutputEvent(String connectionId, String outputName, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.sendOutputEvent(connectionId, outputName, eventBody, handler);
    }

    //Module_WaitForConnectionStatusChange
    @Override
    public void moduleWaitForConnectionStatusChange(String connectionId, Handler<AsyncResult<String>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Module_WaitForDesiredPropertiesPatch
    @Override
    public void moduleWaitForDesiredPropertiesPatch(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        this._moduleGlue.waitForDesiredPropertyPatch(connectionId, handler);
    }

    //Module_WaitForInputMessage
    @Override
    public void moduleWaitForInputMessage(String connectionId, String inputName, Handler<AsyncResult<EventBody>> handler)
    {
        this._moduleGlue.waitForInputMessage(connectionId, inputName, handler);
    }

    //Module_WaitForMethodAndReturnResponse
    @Override
    public void moduleWaitForMethodAndReturnResponse(String connectionId, String methodName, MethodRequestAndResponse requestAndResponse, Handler<AsyncResult<Void>> handler)
    {
        this._moduleGlue.WaitForMethodAndReturnResponse(connectionId, methodName, requestAndResponse, handler);
    }


}
