package glue;

import com.microsoft.azure.sdk.iot.service.exceptions.IotHubException;
import com.microsoft.azure.sdk.iot.service.twin.TwinClient;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.Twin;
import io.vertx.core.AsyncResult;
import io.vertx.core.Future;
import io.vertx.core.Handler;
import io.vertx.core.json.JsonObject;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class RegistryGlue
{
    HashMap<String, TwinClient> _map = new HashMap<>();
    int _clientCount = 0;

    public void connect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler)
    {
        System.out.printf("Connect called%n");
        TwinClient client = new TwinClient(connectionString);

        this._clientCount++;
        String connectionId = "registryClient_" + this._clientCount;
        this._map.put(connectionId, client);

        ConnectResponse cr = new ConnectResponse();
        cr.setConnectionId(connectionId);
        handler.handle(Future.succeededFuture(cr));
    }

    private TwinClient getClient(String connectionId)
    {
        return this._map.getOrDefault(connectionId, null);
    }

    private void _closeConnection(String connectionId)
    {
        System.out.printf("Disconnect for %s%n", connectionId);
        TwinClient client = getClient(connectionId);
        if (client != null)
        {
            this._map.remove(connectionId);
        }
    }

    public void disconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._closeConnection(connectionId);
        handler.handle(Future.succeededFuture());
    }

    public void getModuleTwin(String connectionId, String deviceId, String moduleId, Handler<AsyncResult<Twin>> handler)
    {
        System.out.printf("getModuleTwin called for %s with deviceId = %s and moduleId = %s%n", connectionId, deviceId, moduleId);

        TwinClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            com.microsoft.azure.sdk.iot.service.twin.Twin twin;
            try
            {
                twin = client.get(deviceId, moduleId);
                Twin hortonTwin = new Twin(new JsonObject(twin.getDesiredProperties()), new JsonObject(twin.getReportedProperties()));
                handler.handle(Future.succeededFuture(hortonTwin));
            }
            catch (IOException | IotHubException e)
            {
                handler.handle(Future.failedFuture(e));
            }
        }
    }

    public void sendModuleTwinPatch(String connectionId, String deviceId, String moduleId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        System.out.printf("sendModuleTwinPatch called for %s with deviceId = %s and moduleId = %s%n", connectionId, deviceId, moduleId);
        System.out.println(twin.toString());

        TwinClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            com.microsoft.azure.sdk.iot.service.twin.Twin serviceTwin = new com.microsoft.azure.sdk.iot.service.twin.Twin(deviceId, moduleId);

            Map<String, Object> desiredProps = (Map<String, Object>)twin.getDesired();
            serviceTwin.getDesiredProperties().putAll(desiredProps);

            try
            {
                client.patch(serviceTwin);
            }
            catch (IotHubException | IOException e)
            {
                handler.handle(Future.failedFuture(e));
            }


            handler.handle(Future.succeededFuture());
        }
    }

    public void Cleanup()
    {
        Set<String> keys = this._map.keySet();
        if (!keys.isEmpty())
        {
            for (String key : keys)
            {
                this._closeConnection(key);
            }
        }
    }
}
