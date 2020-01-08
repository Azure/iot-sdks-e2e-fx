package glue;

import io.swagger.server.api.model.LogMessage;
import io.swagger.server.api.verticle.ModuleApiImpl;
import io.swagger.server.api.verticle.RegistryApiImpl;
import io.swagger.server.api.verticle.ServiceApiImpl;
import io.vertx.core.AsyncResult;
import io.vertx.core.Future;
import io.vertx.core.Handler;
import io.vertx.core.json.JsonObject;

public class ControlGlue
{
    public void Cleanup(Handler<AsyncResult<Void>> handler)
    {
        ModuleApiImpl._moduleGlue.Cleanup();
        RegistryApiImpl._registryGlue.Cleanup();
        ServiceApiImpl._serviceGlue.Cleanup();
        handler.handle(Future.succeededFuture());
    }

    public void outputMessage(LogMessage logMessage, Handler<AsyncResult<Void>> handler)
    {
        System.out.println(logMessage.getMessage());
        handler.handle(Future.succeededFuture());
    }

    public void getCapabilities(Handler<AsyncResult<Object>> handler)
    {
        JsonObject caps = new JsonObject("{"+
                "\"flags\": {},"+
                "\"skip_list\": [\"module_under_test_has_device_wrapper\"]" +
                "}");
        handler.handle(Future.succeededFuture(caps));
    }
}
