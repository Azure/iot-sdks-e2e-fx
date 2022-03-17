package glue;

import com.microsoft.azure.sdk.iot.service.exceptions.IotHubException;
import com.microsoft.azure.sdk.iot.service.methods.DirectMethodRequestOptions;
import com.microsoft.azure.sdk.iot.service.methods.DirectMethodsClient;
import com.microsoft.azure.sdk.iot.service.methods.DirectMethodResponse;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.MethodInvoke;
import io.vertx.core.AsyncResult;
import io.vertx.core.Future;
import io.vertx.core.Handler;

import java.io.IOException;
import java.util.HashMap;
import java.util.Set;

public class ServiceGlue
{
    HashMap<String, DirectMethodsClient> _map = new HashMap<>();
    int _clientCount = 0;

    public void connect(String connectionString, Handler<AsyncResult<ConnectResponse>> handler)
    {
        System.out.printf("connect called%n");
        DirectMethodsClient client = new DirectMethodsClient(connectionString);

        this._clientCount++;
        String connectionId = "serviceClient_" + this._clientCount;
        this._map.put(connectionId, client);

        ConnectResponse cr = new ConnectResponse();
        cr.setConnectionId(connectionId);
        handler.handle(Future.succeededFuture(cr));
    }

    private DirectMethodsClient getClient(String connectionId)
    {
        return this._map.getOrDefault(connectionId, null);
    }


    private void _closeConnection(String connectionId)
    {
        System.out.printf("Disconnect for %s%n", connectionId);
        DirectMethodsClient client = getClient(connectionId);
        if (client != null)
        {
            this._map.remove(connectionId);
        }
    }

    public void disconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        _closeConnection(connectionId);
        handler.handle(Future.succeededFuture());
    }

    private void invokeMethodCommon(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        System.out.printf("invoking method on %s with deviceId = %s moduleId = %s%n", connectionId, deviceId, moduleId);
        System.out.println(methodInvokeParameters);

        DirectMethodsClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            String methodName = methodInvokeParameters.getMethodName();
            Object payload = methodInvokeParameters.getPayload();
            DirectMethodRequestOptions requestOptions =
                DirectMethodRequestOptions.builder()
                    .methodResponseTimeoutSeconds(methodInvokeParameters.getResponseTimeoutInSeconds())
                    .methodConnectTimeoutSeconds(methodInvokeParameters.getConnectTimeoutInSeconds())
                    .payload(payload)
                    .build();

            DirectMethodResponse result = null;
            System.out.printf("invoking%n");
            try
            {
                if (moduleId == null)
                {
                    result = client.invoke(deviceId, methodName, requestOptions);
                }
                else
                {
                    result = client.invoke(deviceId, moduleId, methodName, requestOptions);
                }
            }
            catch (IotHubException e)
            {
                handler.handle(Future.failedFuture(e));
            } catch (IOException e)
            {
                e.printStackTrace();
            }
            System.out.printf("invoke returned%n");
            System.out.println(result);
            handler.handle(Future.succeededFuture(result));
        }
    }

    public void invokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        invokeMethodCommon(connectionId, deviceId, null, methodInvokeParameters, handler);

    }

    public void invokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        invokeMethodCommon(connectionId, deviceId, moduleId, methodInvokeParameters, handler);
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
