package io.swagger.server.api.verticle;

import io.swagger.server.api.model.Certificate;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface ModuleApi  {
    //Module_Connect
    void moduleConnect(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler);

    //Module_Connect2
    void moduleConnect2(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_ConnectFromEnvironment
    void moduleConnectFromEnvironment(String transportType, Handler<AsyncResult<ConnectResponse>> handler);

    //Module_CreateFromConnectionString
    void moduleCreateFromConnectionString(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler);

    //Module_CreateFromEnvironment
    void moduleCreateFromEnvironment(String transportType, Handler<AsyncResult<ConnectResponse>> handler);

    //Module_CreateFromX509
    void moduleCreateFromX509(String transportType, Object x509, Handler<AsyncResult<ConnectResponse>> handler);

    //Module_Destroy
    void moduleDestroy(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_Disconnect
    void moduleDisconnect(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_Disconnect2
    void moduleDisconnect2(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_EnableInputMessages
    void moduleEnableInputMessages(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_EnableMethods
    void moduleEnableMethods(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_EnableTwin
    void moduleEnableTwin(String connectionId, Handler<AsyncResult<Void>> handler);

    //Module_GetConnectionStatus
    void moduleGetConnectionStatus(String connectionId, Handler<AsyncResult<String>> handler);

    //Module_GetTwin
    void moduleGetTwin(String connectionId, Handler<AsyncResult<Twin>> handler);

    //Module_InvokeDeviceMethod
    void moduleInvokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler);

    //Module_InvokeModuleMethod
    void moduleInvokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler);

    //Module_PatchTwin
    void modulePatchTwin(String connectionId, Twin twin, Handler<AsyncResult<Void>> handler);

    //Module_Reconnect
    void moduleReconnect(String connectionId, Boolean forceRenewPassword, Handler<AsyncResult<Void>> handler);

    //Module_SendEvent
    void moduleSendEvent(String connectionId, EventBody eventBody, Handler<AsyncResult<Void>> handler);

    //Module_SendOutputEvent
    void moduleSendOutputEvent(String connectionId, String outputName, EventBody eventBody, Handler<AsyncResult<Void>> handler);

    //Module_WaitForConnectionStatusChange
    void moduleWaitForConnectionStatusChange(String connectionId, Handler<AsyncResult<String>> handler);

    //Module_WaitForDesiredPropertiesPatch
    void moduleWaitForDesiredPropertiesPatch(String connectionId, Handler<AsyncResult<Twin>> handler);

    //Module_WaitForInputMessage
    void moduleWaitForInputMessage(String connectionId, String inputName, Handler<AsyncResult<EventBody>> handler);

    //Module_WaitForMethodAndReturnResponse
    void moduleWaitForMethodAndReturnResponse(String connectionId, String methodName, MethodRequestAndResponse requestAndResponse, Handler<AsyncResult<Void>> handler);

}
