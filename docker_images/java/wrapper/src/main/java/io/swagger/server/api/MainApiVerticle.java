package io.swagger.server.api;

import java.nio.charset.Charset;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;

import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.github.phiz71.vertx.swagger.router.OperationIdServiceIdResolver;
import com.github.phiz71.vertx.swagger.router.SwaggerRouter;

import io.swagger.models.Swagger;
import io.swagger.parser.SwaggerParser;
import io.vertx.core.AbstractVerticle;
import io.vertx.core.Context;
import io.vertx.core.Future;
import io.vertx.core.json.Json;
import io.vertx.core.logging.Logger;
import io.vertx.core.logging.LoggerFactory;
import io.vertx.core.Vertx;
import io.vertx.ext.web.Router;

// Added 3 lines in merge
import java.util.function.Function;
import io.vertx.core.eventbus.DeliveryOptions;
import io.vertx.ext.web.RoutingContext;

public class MainApiVerticle extends AbstractVerticle {
    final static Logger LOGGER = LoggerFactory.getLogger(MainApiVerticle.class);

    private int serverPort = 8080;
    protected Router router;

    public int getServerPort() {
        return serverPort;
    }

    public void setServerPort(int serverPort) {
        this.serverPort = serverPort;
    }

    @Override
    public void init(Vertx vertx, Context context) {
        super.init(vertx, context);
        router = Router.router(vertx);
    }

    @Override
    public void start(Future<Void> startFuture) throws Exception {
        Json.mapper.registerModule(new JavaTimeModule());

        // Read swagger.json from classpath resources directly (more reliable
        // than Vert.x FileSystem which depends on FileResolver cache behaviour).
        String swaggerContent;
        try {
            InputStream is = MainApiVerticle.class.getClassLoader().getResourceAsStream("swagger.json");
            if (is == null) {
                startFuture.fail("swagger.json not found on classpath");
                return;
            }
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int length;
            while ((length = is.read(buffer)) != -1) {
                result.write(buffer, 0, length);
            }
            swaggerContent = result.toString("UTF-8");
            is.close();
        } catch (Exception e) {
            LOGGER.error("Failed to read swagger.json from classpath", e);
            startFuture.fail(e);
            return;
        }

        Swagger swagger = new SwaggerParser().parse(swaggerContent);
        // Changed constructor in merge to add setSendTimeout()
        Router swaggerRouter = SwaggerRouter.swaggerRouter(router, swagger, vertx.eventBus(), new OperationIdServiceIdResolver(), new Function<RoutingContext, DeliveryOptions>() {
            @Override
            public DeliveryOptions apply(RoutingContext t) {
                return new DeliveryOptions().setSendTimeout(90000);
            }
        });
        deployVerticles(startFuture);

        vertx.createHttpServer()
            .requestHandler(swaggerRouter::accept)
            .listen(serverPort, h -> {
                if (h.succeeded()) {
                    startFuture.complete();
                } else {
                    LOGGER.error("HTTP server failed to start", h.cause());
                    startFuture.fail(h.cause());
                }
            });
    }

    public void deployVerticles(Future<Void> startFuture) {

        vertx.deployVerticle("io.swagger.server.api.verticle.ControlApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("ControlApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("ControlApiVerticle : Deployment failed", res.cause());
            }
        });

        vertx.deployVerticle("io.swagger.server.api.verticle.DeviceApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("DeviceApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("DeviceApiVerticle : Deployment failed", res.cause());
            }
        });

        vertx.deployVerticle("io.swagger.server.api.verticle.ModuleApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("ModuleApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("ModuleApiVerticle : Deployment failed", res.cause());
            }
        });

        vertx.deployVerticle("io.swagger.server.api.verticle.NetApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("NetApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("NetApiVerticle : Deployment failed", res.cause());
            }
        });

        vertx.deployVerticle("io.swagger.server.api.verticle.RegistryApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("RegistryApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("RegistryApiVerticle : Deployment failed", res.cause());
            }
        });

        vertx.deployVerticle("io.swagger.server.api.verticle.ServiceApiVerticle", res -> {
            if (res.succeeded()) {
                LOGGER.info("ServiceApiVerticle : Deployed");
            } else {
                startFuture.fail(res.cause());
                LOGGER.error("ServiceApiVerticle : Deployment failed", res.cause());
            }
        });

    }
}