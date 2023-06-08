package io.swagger.server.api.verticle;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.Twin;

import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

public interface RegistryApi  {
    //Registry_Connect
    void registryConnect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler);

    //Registry_Disconnect
    void registryDisconnect(String connectionId, Handler<AsyncResult<Void>> handler);

    //Registry_GetDeviceTwin
    void registryGetDeviceTwin(String connectionId, String deviceId, Handler<AsyncResult<Twin>> handler);

    //Registry_GetModuleTwin
    void registryGetModuleTwin(String connectionId, String deviceId, String moduleId, Handler<AsyncResult<Twin>> handler);

    //Registry_PatchDeviceTwin
    void registryPatchDeviceTwin(String connectionId, String deviceId, Twin twin, Handler<AsyncResult<Void>> handler);

    //Registry_PatchModuleTwin
    void registryPatchModuleTwin(String connectionId, String deviceId, String moduleId, Twin twin, Handler<AsyncResult<Void>> handler);

}
