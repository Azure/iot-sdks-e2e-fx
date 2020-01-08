package glue;

import com.microsoft.azure.sdk.iot.deps.twin.TwinCollection;
import com.microsoft.azure.sdk.iot.service.devicetwin.DeviceTwin;
import com.microsoft.azure.sdk.iot.service.devicetwin.DeviceTwinDevice;
import com.microsoft.azure.sdk.iot.service.devicetwin.Pair;
import com.microsoft.azure.sdk.iot.service.exceptions.IotHubException;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.Twin;
import io.vertx.core.AsyncResult;
import io.vertx.core.Future;
import io.vertx.core.Handler;
import io.vertx.core.json.JsonObject;

import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class RegistryGlue
{
    HashMap<String, DeviceTwin> _map = new HashMap<>();
    int _clientCount = 0;

    public void connect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler)
    {
        System.out.printf("Connect called%n");
        try
        {
            DeviceTwin client = DeviceTwin.createFromConnectionString(connectionString);

            this._clientCount++;
            String connectionId = "registryClient_" + this._clientCount;
            this._map.put(connectionId, client);

            ConnectResponse cr = new ConnectResponse();
            cr.setConnectionId(connectionId);
            handler.handle(Future.succeededFuture(cr));
        } catch (IOException e)
        {
            handler.handle(Future.failedFuture(e));
        }
    }

    private DeviceTwin getClient(String connectionId)
    {
        if (this._map.containsKey(connectionId))
        {
            return this._map.get(connectionId);
        }
        else
        {
            return null;
        }
    }

    private void _closeConnection(String connectionId)
    {
        System.out.printf("Disconnect for %s%n", connectionId);
        DeviceTwin client = getClient(connectionId);
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

    private TwinCollection setToMap(Set<Pair> set)
    {
        TwinCollection map = new TwinCollection();

        if (set != null)
        {
            for (Pair p : set)
            {
                if (map.containsKey(p.getKey()))
                {
                    throw new IllegalArgumentException("Set must not contain multiple pairs with the same keys. Duplicate key: " + p.getKey());
                }

                map.putFinal(p.getKey(), p.getValue());
            }
        }

        return map;
    }

    public void getModuleTwin(String connectionId, String deviceId, String moduleId, Handler<AsyncResult<Twin>> handler)
    {
        System.out.printf("getModuleTwin called for %s with deviceId = %s and moduleId = %s%n", connectionId, deviceId, moduleId);

        DeviceTwin client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            DeviceTwinDevice twin = new DeviceTwinDevice(deviceId, moduleId);
            try
            {
                client.getTwin(twin);
            } catch (IOException | IotHubException e)
            {
                handler.handle(Future.failedFuture(e));
            }
            Twin hortonTwin = new Twin(new JsonObject(setToMap(twin.getDesiredProperties())), new JsonObject(setToMap(twin.getReportedProperties())));
            handler.handle(Future.succeededFuture(hortonTwin));
        }
    }

    public void sendModuleTwinPatch(String connectionId, String deviceId, String moduleId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        System.out.printf("sendModuleTwinPatch called for %s with deviceId = %s and moduleId = %s%n", connectionId, deviceId, moduleId);
        System.out.println(twin.toString());

        DeviceTwin client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            DeviceTwinDevice serviceTwin = new DeviceTwinDevice(deviceId, moduleId);

            Set<Pair> newProps = new HashSet<Pair>();
            Map<String, Object> desiredProps = (Map<String, Object>)twin.getDesired();
            for (String key : desiredProps.keySet())
            {
                newProps.add(new Pair(key, desiredProps.get(key)));
            }
            serviceTwin.setDesiredProperties(newProps);
            try
            {
                client.updateTwin(serviceTwin);
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
