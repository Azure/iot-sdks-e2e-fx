package io.swagger.server.api.verticle;

import io.swagger.server.api.MainApiException;

public final class NetApiException extends MainApiException {
    public NetApiException(int statusCode, String statusMessage) {
        super(statusCode, statusMessage);
    }



}