package io.swagger.server.api.verticle;

import io.swagger.server.api.model.LogMessage;
import io.swagger.server.api.MainApiException;

public final class ControlApiException extends MainApiException {
    public ControlApiException(int statusCode, String statusMessage) {
        super(statusCode, statusMessage);
    }



}