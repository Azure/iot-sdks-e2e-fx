package io.swagger.server.api.verticle;

import io.swagger.server.api.model.Certificate;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface DeviceApi  {
    //Device_Connect
    void deviceConnect(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler);

    //Device_Connect2
    void deviceConnect2(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_CreateFromConnectionString
    void deviceCreateFromConnectionString(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler);

    //Device_CreateFromX509
    void deviceCreateFromX509(String transportType, Object x509, Handler<AsyncResult<ConnectResponse>> handler);

    //Device_Destroy
    void deviceDestroy(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_Disconnect
    void deviceDisconnect(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_Disconnect2
    void deviceDisconnect2(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_EnableC2dMessages
    void deviceEnableC2dMessages(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_EnableMethods
    void deviceEnableMethods(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_EnableTwin
    void deviceEnableTwin(String connectionId, Handler<AsyncResult<Void>> handler);

    //Device_GetConnectionStatus
    void deviceGetConnectionStatus(String connectionId, Handler<AsyncResult<String>> handler);

    //Device_GetTwin
    void deviceGetTwin(String connectionId, Handler<AsyncResult<Twin>> handler);

    //Device_PatchTwin
    void devicePatchTwin(String connectionId, Twin twin, Handler<AsyncResult<Void>> handler);

    //Device_Reconnect
    void deviceReconnect(String connectionId, Boolean forceRenewPassword, Handler<AsyncResult<Void>> handler);

    //Device_SendEvent
    void deviceSendEvent(String connectionId, EventBody eventBody, Handler<AsyncResult<Void>> handler);

    //Device_WaitForC2dMessage
    void deviceWaitForC2dMessage(String connectionId, Handler<AsyncResult<EventBody>> handler);

    //Device_WaitForConnectionStatusChange
    void deviceWaitForConnectionStatusChange(String connectionId, Handler<AsyncResult<String>> handler);

    //Device_WaitForDesiredPropertiesPatch
    void deviceWaitForDesiredPropertiesPatch(String connectionId, Handler<AsyncResult<Twin>> handler);

    //Device_WaitForMethodAndReturnResponse
    void deviceWaitForMethodAndReturnResponse(String connectionId, String methodName, MethodRequestAndResponse requestAndResponse, Handler<AsyncResult<Void>> handler);

}
