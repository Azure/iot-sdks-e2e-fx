package glue;

import com.microsoft.azure.sdk.iot.device.ClientOptions;
import com.microsoft.azure.sdk.iot.device.IotHubClientProtocol;
import com.microsoft.azure.sdk.iot.device.IotHubEventCallback;
import com.microsoft.azure.sdk.iot.device.IotHubMessageResult;
import com.microsoft.azure.sdk.iot.device.IotHubStatusCode;
import com.microsoft.azure.sdk.iot.device.Message;
import com.microsoft.azure.sdk.iot.device.ModuleClient;
import com.microsoft.azure.sdk.iot.device.auth.IotHubSSLContext;
import com.microsoft.azure.sdk.iot.device.edge.DirectMethodRequest;
import com.microsoft.azure.sdk.iot.device.exceptions.ModuleClientException;
import com.microsoft.azure.sdk.iot.device.twin.DirectMethodPayload;
import com.microsoft.azure.sdk.iot.device.twin.DirectMethodResponse;
import com.microsoft.azure.sdk.iot.device.twin.MethodCallback;
import com.microsoft.azure.sdk.iot.device.twin.Property;
import com.microsoft.azure.sdk.iot.device.twin.TwinCollection;
import io.swagger.server.api.MainApiException;
import io.swagger.server.api.model.Certificate;
import io.swagger.server.api.model.ConnectResponse;
import io.swagger.server.api.model.EventBody;
import io.swagger.server.api.model.MethodInvoke;
import io.swagger.server.api.model.MethodRequestAndResponse;
import io.swagger.server.api.model.Twin;
import io.vertx.core.AsyncResult;
import io.vertx.core.Future;
import io.vertx.core.Handler;
import io.vertx.core.json.Json;
import io.vertx.core.json.JsonObject;

import java.io.IOException;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.Timer;
import java.util.TimerTask;
import java.util.concurrent.TimeoutException;


public class ModuleGlue
{
    private IotHubClientProtocol transportFromString(String protocolStr)
    {
        IotHubClientProtocol protocol = null;

        if (protocolStr.equals("amqp"))
        {
            protocol = IotHubClientProtocol.AMQPS;
        }
        else if (protocolStr.equals("mqtt"))
        {
            protocol = IotHubClientProtocol.MQTT;
        }
        else if (protocolStr.equals("amqpws"))
        {
            protocol = IotHubClientProtocol.AMQPS_WS;
        }
        else if (protocolStr.equals("mqttws"))
        {
            protocol = IotHubClientProtocol.MQTT_WS;
        }
        else if (protocolStr.equals("http"))
        {
            protocol = IotHubClientProtocol.HTTPS;
        }
        return protocol;
    }

    HashMap<String, ModuleClient> _map = new HashMap<>();
    int _clientCount = 0;

    public void connectFromEnvironment(String transportType, Handler<AsyncResult<ConnectResponse>> handler)
    {
        System.out.printf("ConnectFromEnvironment called with transport %s%n", transportType);

        IotHubClientProtocol protocol = this.transportFromString(transportType);
        if (protocol == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid transport")));
            return;
        }

        try
        {
            ModuleClient client = ModuleClient.createFromEnvironment(new UnixDomainSocketChannelImpl(), protocol);
            client.open(true);

            this._clientCount++;
            String connectionId = "moduleClient_" + this._clientCount;
            this._map.put(connectionId, client);

            ConnectResponse cr = new ConnectResponse();
            cr.setConnectionId(connectionId);
            handler.handle(Future.succeededFuture(cr));
        } catch (Exception e)
        {
            handler.handle(Future.failedFuture(e));
        }
    }

    private ModuleClient getClient(String connectionId)
    {
        return this._map.getOrDefault(connectionId, null);
    }

    public void connect(String transportType, String connectionString, Certificate caCertificate, Handler<AsyncResult<ConnectResponse>> handler)
    {
        System.out.printf("Connect called with transport %s%n", transportType);

        IotHubClientProtocol protocol = this.transportFromString(transportType);
        if (protocol == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid transport")));
            return;
        }

        try
        {
            String cert = caCertificate.getCert();
            ClientOptions.ClientOptionsBuilder clientOptionsBuilder = ClientOptions.builder();
            if (cert != null && !cert.isEmpty())
            {
                clientOptionsBuilder.sslContext(IotHubSSLContext.getSSLContextFromFile(cert));
            }

            ModuleClient client = new ModuleClient(connectionString, protocol, clientOptionsBuilder.build());

            client.open(true);

            this._clientCount++;
            String connectionId = "moduleClient_" + this._clientCount;
            this._map.put(connectionId, client);

            ConnectResponse cr = new ConnectResponse();
            cr.setConnectionId(connectionId);
            handler.handle(Future.succeededFuture(cr));
        } catch (Exception e)
        {
            handler.handle(Future.failedFuture(e));
        }
    }


    public void invokeDeviceMethod(String connectionId, String deviceId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            DirectMethodRequest request = new DirectMethodRequest(methodInvokeParameters.getMethodName(), Json.encode(methodInvokeParameters.getPayload()), methodInvokeParameters.getResponseTimeoutInSeconds(), methodInvokeParameters.getConnectTimeoutInSeconds());
            try
            {
                com.microsoft.azure.sdk.iot.device.edge.DirectMethodResponse result = client.invokeMethod(deviceId, request);
                handler.handle(Future.succeededFuture(makeMethodResultThatEncodesCorrectly(result)));
            } catch (Exception e)
            {
                handler.handle(Future.failedFuture(e));
            }
        }
    }

    private void _closeConnection(String connectionId)
    {
        System.out.printf("Disconnect for %s%n", connectionId);
        ModuleClient client = getClient(connectionId);
        if (client != null)
        {
            this._deviceTwinStatusCallback.setHandler(null);
            client.close();
            this._map.remove(connectionId);
        }
    }

    public void disconnect(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        this._closeConnection(connectionId);
        handler.handle(Future.succeededFuture());
    }

    public void enableInputMessages(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            handler.handle(Future.succeededFuture());
        }
    }

    private Twin _twin = null;
    private Handler<AsyncResult<Twin>> _twinHandler;
    private Timer _timer = null;

    public void setTwinHandler(Handler<AsyncResult<Twin>> handler)
    {
        if (handler == null)
        {
            this._twin = null;
        }
        else
        {
            this._twin = new Twin(new JsonObject(), new JsonObject());

        }
        this._twinHandler = handler;
    }

    public void onPropertyChanged(Property property, Object context)
    {
        System.out.println(
            "onProperty callback for " + (property.getIsReported() ? "reported" : "desired") +
                " property " + property.getKey() +
                " to " + property.getValue() +
                ", Properties version:" + property.getVersion());
        if (this._twin == null)
        {
            System.out.println("nobody is listening for desired properties.  ignoring.");
        }
        else
        {
            if (property.getIsReported())
            {
                ((JsonObject) this._twin.getReported()).getMap().put(property.getKey(), property.getValue());
            }
            else
            {
                ((JsonObject) this._twin.getDesired()).getMap().put(property.getKey(), property.getValue());
            }
            System.out.println(this._twin.toString());
            System.out.println("scheduling timer");
            this.rescheduleTwinHandler();
        }
    }

    private void rescheduleTwinHandler()
    {
        if (_twinHandler == null)
        {
            return;
        }
        // call _handler 2 seconds after the last designed property change
        if (this._timer != null)
        {
            this._timer.cancel();
            this._timer = null;
        }
        this._timer = new Timer();
        this._timer.schedule(new TimerTask()
        {
            @Override
            public void run()
            {
                _timer = null;
                if (_twinHandler != null && _twin != null)
                {
                    System.out.println("It's been 2 seconds since last desired property arrived.  Calling handler");
                    System.out.println(_twin.toString());
                    _twinHandler.handle(Future.succeededFuture(_twin));
                    _twinHandler = null;
                }
            }
        }, 2000);
    }

    private static class IotHubEventCallbackImpl implements IotHubEventCallback
    {
        Handler<AsyncResult<Void>> _handler = null;

        public void setHandler(Handler<AsyncResult<Void>> handler)
        {
            this._handler = handler;
        }

        @Override
        public void execute(IotHubStatusCode status, Object context)
        {
            System.out.println("IoT Hub responded to operation with status " + status.name());
            Handler<AsyncResult<Void>> handler = this._handler;
            this._handler = null;
            if (handler != null)
            {
                if (status == IotHubStatusCode.OK)
                {
                    handler.handle(Future.succeededFuture());
                }
                else
                {
                    handler.handle(Future.failedFuture(new MainApiException(500, "operation failed")));
                }
            }
        }
    }

    private IotHubEventCallbackImpl _deviceTwinStatusCallback = new IotHubEventCallbackImpl();

    public void enableTwin(String connectionId, final Handler<AsyncResult<Void>> handler)
    {
        final ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            try
            {
                System.out.println("calling subscribeToDesiredProperties to start twin");
                client.subscribeToDesiredProperties(
                    (twin, context) ->
                    {
                        TwinCollection desiredProperties = twin.getDesiredProperties();
                        for (String key : desiredProperties.keySet())
                        {
                            onPropertyChanged(new Property(key, desiredProperties.get(key)), null);
                        }
                    },
                    null);

                handler.handle(Future.succeededFuture());
            }
            catch (Exception e)
            {
                handler.handle(Future.failedFuture((e)));
            }
        }
    }

    private static class EventCallback implements IotHubEventCallback
    {
        Handler<AsyncResult<Void>> _handler;

        public EventCallback(Handler<AsyncResult<Void>> handler)
        {
            this._handler = handler;
        }

        public synchronized void execute(IotHubStatusCode status, Object context)
        {
            System.out.printf("EventCallback called with status %s%n", status.toString());
            this._handler.handle(Future.succeededFuture());
        }
    }

    private void sendEventHelper(String connectionId, Message msg, Handler<AsyncResult<Void>> handler)
    {
        System.out.println("inside sendEventHelper");

        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            EventCallback callback = new EventCallback(handler);
            System.out.printf("calling sendEventAsync%n");
            client.sendEventAsync(msg, callback, null);
        }
    }

    public void sendEvent(String connectionId, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        System.out.printf("moduleConnectionIdEventPut called for %s%n", connectionId);
        System.out.println(eventBody);
        this.sendEventHelper(connectionId, new Message(Json.encode(eventBody.getBody())), handler);
    }

    protected static class MessageCallback implements com.microsoft.azure.sdk.iot.device.MessageCallback
    {
        ModuleClient _client;
        Handler<AsyncResult<EventBody>> _handler;
        String _inputName;

        public MessageCallback(ModuleClient client, String inputName, Handler<AsyncResult<EventBody>> handler)
        {
            this._client = client;
            this._inputName = inputName;
            this._handler = handler;
        }

        public synchronized IotHubMessageResult execute(Message msg, Object context)
        {
            System.out.println("MessageCallback called");
            this._client.setMessageCallback(this._inputName, null, null);
            String result = new String(msg.getBytes(), Message.DEFAULT_IOTHUB_MESSAGE_CHARSET);
            System.out.printf("result = %s%n", result);
            if (this._handler != null)
            {
                this._handler.handle(Future.succeededFuture(new EventBody(new JsonObject(result), new JsonObject(), new JsonObject())));
            }
            return IotHubMessageResult.COMPLETE;
        }
    }

    public void waitForInputMessage(String connectionId, String inputName, Handler<AsyncResult<EventBody>> handler)
    {
        System.out.printf("waitForInputMessage with %s, %s%n", connectionId, inputName);

        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            MessageCallback callback = new MessageCallback(client, inputName, handler);
            System.out.printf("calling setMessageCallback%n");
            client.setMessageCallback(inputName, callback, null);
        }
    }

    private static class DeviceMethodCallbackImpl implements MethodCallback
    {
        public Handler<AsyncResult<Void>> _handler;
        public String _requestBody;
        public String _responseBody;
        public String _methodName;
        public int _statusCode;
        public ModuleClient _client;

        public void reset()
        {
            this._methodName = null;
            this._handler = null;
        }

        @Override
        public DirectMethodResponse onMethodInvoked(String methodName, DirectMethodPayload methodData, Object context)
        {
            System.out.printf("method %s called%n", methodName);
            if (methodName.equals(this._methodName))
            {
                System.out.println("Received payload:");
                System.out.println(methodData.getPayloadAsJsonString());

                Object methodDataObject = methodData.getPayload(Map.class);
                System.out.printf("methodData: %s%n", methodDataObject);

                if (methodDataObject.equals(this._requestBody) ||
                    Json.encode(methodDataObject).equals(this._requestBody))
                {
                    System.out.printf("Method data looks correct.  Returning result: %s%n", _responseBody);
                    this._handler.handle(Future.succeededFuture());
                    this.reset();
                    return new DirectMethodResponse(this._statusCode, this._responseBody);
                }
                else
                {
                    System.out.printf("method data does not match.  Expected %s%n", this._requestBody);
                    this._handler.handle(Future.failedFuture("methodData does not match"));
                    this.reset();
                    return new DirectMethodResponse(500, "methodData not received as expected");
                }
            }
            else
            {
                this._handler.handle(Future.failedFuture("unexpected call: " + methodName));
                this.reset();
                return new DirectMethodResponse(404, "method " + methodName + " not handled");
            }
        }
    }

    DeviceMethodCallbackImpl _methodCallback = new DeviceMethodCallbackImpl();

    public void enableMethods(String connectionId, Handler<AsyncResult<Void>> handler)
    {
        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            IotHubEventCallbackImpl callback = new IotHubEventCallbackImpl();
            callback.setHandler(handler);
            client.subscribeToMethodsAsync(this._methodCallback, null, callback, null);
        }
    }

    public void WaitForMethodAndReturnResponse(String connectionId, String methodName, MethodRequestAndResponse requestAndResponse, Handler<AsyncResult<Void>> handler)
    {
        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            _methodCallback._handler = handler;
            _methodCallback._requestBody = Json.encode(((LinkedHashMap) requestAndResponse.getRequestPayload()).get("payload"));
            _methodCallback._responseBody = Json.encode(requestAndResponse.getResponsePayload());
            _methodCallback._statusCode = requestAndResponse.getStatusCode();
            _methodCallback._client = client;
            _methodCallback._methodName = methodName;
        }
    }

    private JsonObject makeMethodResultThatEncodesCorrectly(com.microsoft.azure.sdk.iot.device.edge.DirectMethodResponse result)
    {
        // Our JSON encoder doesn't like the way the MethodClass implements getPayload and getPayloadObject.  It
        // produces JSON that had both fields and the we want to return payloadObject, but we want to return it
        // in the field called "payload".  The easiest workaroudn is to make an empty JsonObject and copy the
        // values over manually.  I'm sure there's a better way, but this is test code.
        JsonObject fixedObject = new JsonObject();
        fixedObject.put("status", result.getStatus());

        // The payload type in DirectMethodRequest is a json string generated by Json.encode(),
        // so we get the payload as a json string as well on the response side.
        fixedObject.put("payload", result.getPayloadAsJsonString());
        return fixedObject;
    }


    public void invokeModuleMethod(String connectionId, String deviceId, String moduleId, MethodInvoke methodInvokeParameters, Handler<AsyncResult<Object>> handler)
    {
        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            DirectMethodRequest request = new DirectMethodRequest(methodInvokeParameters.getMethodName(), Json.encode(methodInvokeParameters.getPayload()), methodInvokeParameters.getResponseTimeoutInSeconds(), methodInvokeParameters.getConnectTimeoutInSeconds());
            try
            {
                com.microsoft.azure.sdk.iot.device.edge.DirectMethodResponse result = client.invokeMethod(deviceId, moduleId, request);
                handler.handle(Future.succeededFuture(makeMethodResultThatEncodesCorrectly(result)));
            } catch (Exception e)
            {
                handler.handle(Future.failedFuture(e));
            }
        }
    }

    public void sendOutputEvent(String connectionId, String outputName, EventBody eventBody, Handler<AsyncResult<Void>> handler)
    {
        System.out.printf("sendOutputEvent called for %s, %s%n", connectionId, outputName);
        System.out.println(eventBody);
        Message msg = new Message(Json.encode(eventBody.getBody()));
        msg.setOutputName(outputName);
        this.sendEventHelper(connectionId, msg, handler);
    }

    public void waitForDesiredPropertyPatch(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        System.out.printf("waitForDesiredPropertyPatch with %s%n", connectionId);

        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            this.setTwinHandler(res -> {
                if (res.succeeded())
                {
                    handler.handle(Future.succeededFuture(res.result()));
                }
                else
                {
                    handler.handle(res);
                }
            });

        }
    }

    public void getTwin(String connectionId, Handler<AsyncResult<Twin>> handler)
    {
        System.out.printf("getTwin with %s%n", connectionId);

        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            this.setTwinHandler(handler);
            try
            {
                com.microsoft.azure.sdk.iot.device.twin.Twin twin = client.getTwin();
                TwinCollection desiredProperties = twin.getDesiredProperties();
                for (String key : desiredProperties.keySet())
                {
                    onPropertyChanged(new Property(key, desiredProperties.get(key)), null);
                }
            } catch (Exception e)
            {
                this.setTwinHandler(null);
                handler.handle(Future.failedFuture(e));
            }
        }
    }

    public void sendTwinPatch(String connectionId, Twin twin, Handler<AsyncResult<Void>> handler)
    {
        System.out.printf("sendTwinPatch called for %s%n", connectionId);
        System.out.println(twin.toString());

        ModuleClient client = getClient(connectionId);
        if (client == null)
        {
            handler.handle(Future.failedFuture(new MainApiException(500, "invalid connection id")));
        }
        else
        {
            TwinCollection reportedProperties = new TwinCollection((LinkedHashMap<String, Object>)twin.getReported());
            System.out.println("reported properties size" + reportedProperties.size());
            System.out.println("reported properties:" + reportedProperties);
            this._deviceTwinStatusCallback.setHandler(handler);
            try
            {
                client.updateReportedProperties(reportedProperties);
                handler.handle(Future.succeededFuture());
            }
            catch (Exception e)
            {
                this._deviceTwinStatusCallback.setHandler(null);
                handler.handle(Future.failedFuture(e));
            }
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
