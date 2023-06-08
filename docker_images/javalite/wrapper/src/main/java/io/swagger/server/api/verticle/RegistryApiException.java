package io.swagger.server.api.verticle;

import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.Twin;

public final class RegistryApiException extends MainApiException {
    public RegistryApiException(int statusCode, String statusMessage) {
        super(statusCode, statusMessage);
    }



}