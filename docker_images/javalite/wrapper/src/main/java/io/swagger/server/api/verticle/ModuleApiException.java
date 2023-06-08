package io.swagger.server.api.verticle;

import io.swagger.server.api.model.Certificate;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;

public final class ModuleApiException extends MainApiException {
    public ModuleApiException(int statusCode, String statusMessage) {
        super(statusCode, statusMessage);
    }



}