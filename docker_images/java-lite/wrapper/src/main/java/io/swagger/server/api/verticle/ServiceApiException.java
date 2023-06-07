package io.swagger.server.api.verticle;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.MethodInvoke;

public final class ServiceApiException extends MainApiException {
    public ServiceApiException(int statusCode, String statusMessage) {
        super(statusCode, statusMessage);
    }



}