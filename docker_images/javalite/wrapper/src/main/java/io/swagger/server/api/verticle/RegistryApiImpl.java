package io.swagger.server.api.verticle;

// Added 1 line in merge
import glue.RegistryGlue;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.MainApiException;

import io.swagger.server.api.model.Twin;
import io.vertx.core.AsyncResult;
import io.vertx.core.Handler;

import java.util.List;
import java.util.Map;

// Added all Override annotations and method bodies in merge

// Changed from interface to class in merge
public class RegistryApiImpl implements RegistryApi
{
    // Added 1 line in merge
    public static RegistryGlue _registryGlue = new RegistryGlue();

    //Registry_Connect
    @Override
    public void registryConnect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler)
    {
        this._registryGlue.connect(connectionString, handler);
    }

    //Registry_Disconnect
    @Override
    public void registryDisconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._registryGlue.disconnect(connectionId, handler);
    }

    //Registry_GetDeviceTwin
    @Override
    public void registryGetDeviceTwin(String connectionId, String deviceId, Handler<AsyncResult<Twin>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Registry_GetModuleTwin
    public void registryGetModuleTwin(String connectionId, String deviceId, String moduleId, Handler<AsyncResult<Twin>> handler)
    {
        this._registryGlue.getModuleTwin(connectionId, deviceId, moduleId, handler);
    }

    //Registry_PatchDeviceTwin
    @Override
    public void registryPatchDeviceTwin(String connectionId, String deviceId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        throw new java.lang.UnsupportedOperationException("Not supported yet");
    }

    //Registry_PatchModuleTwin
    @Override
    public void registryPatchModuleTwin(String connectionId, String deviceId, String moduleId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        this._registryGlue.sendModuleTwinPatch(connectionId, deviceId, moduleId, twin, handler);
    }

}
