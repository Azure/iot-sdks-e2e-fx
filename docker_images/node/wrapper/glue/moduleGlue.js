// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var ModuleClient = require('azure-iot-device').ModuleClient;
var Message = require('azure-iot-device').Message;
var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');
var NamedObjectCache = require('./NamedObjectCache');
var internalGlue = require('./internalGlue')

/**
 * cache of objects.  Used to return object by name to the caller.
 */
var objectCache = new NamedObjectCache();

/**
 * Connect to the azure IoT Hub as a module
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.module_Connect = function(transportType,connectionString,caCertificate) {
  return glueUtils.returnNotImpl();
}


/**
 * Connect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Connect2 = function(connectionId) {
  return internalGlue.internal_Connect2(objectCache, connectionId)
}


/**
 * Connect to the azure IoT Hub as a module using the environment variables
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_ConnectFromEnvironment = function(transportType) {
  return glueUtils.returnNotImpl();
}



/**
 * Create a module client from a connection string
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.module_CreateFromConnectionString = function(transportType,connectionString,caCertificate) {
  return internalGlue.internal_CreateFromConnectionString(objectCache, ModuleClient, transportType, connectionString, caCertificate);
}


/**
 * Create a module client using the EdgeHub environment
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_CreateFromEnvironment = function(transportType) {
  debug(`module_CreateFromEnvironment called with transport ${transportType}`);
  
  return new Promise((resolve, reject) => {  
    resolve(ModuleClient.fromEnvironment(glueUtils.transportFromType(transportType)));
  })
  .then((client) => {
    const connectionId = objectCache.addObject('ModuleClient', client);
    return {"connectionId": connectionId};
  });
}


/**
 * Create a module client from X509 credentials
 *
 * transportType String Transport to use
 * x509 Object
 * returns connectResponse
 **/
exports.module_CreateFromX509 = function(transportType,x509) {
  return glueUtils.returnNotImpl();
}


/**
 * Disonnect and destroy the module client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Destroy = function(connectionId) {
  return internalGlue.internal_Destroy(objectCache, connectionId);
}


/**
 * Disconnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect = function(connectionId) {
  return internalGlue.internal_Disconnect(objectCache, connectionId);
}


/**
 * Disonnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect2 = function(connectionId) {
  return internalGlue.internal_Disconnect2(objectCache, connectionId);
}


/**
 * Enable input messages
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableInputMessages = function(connectionId) {
  debug(`module_EnableInputMessages called with ${connectionId}`);
  return glueUtils.makePromise('module_EnableInputMessages', function(callback) {
    var client = objectCache.getObject(connectionId)
    client.on('inputMessage', function() {});
    callback();
  });
}


/**
 * Enable methods
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableMethods = function(connectionId) {
  return internalGlue.internal_EnableMethods(objectCache, connectionId);
}


/**
 * Enable module twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableTwin = function(connectionId) {
  return internalGlue.internal_EnableTwin(objectCache, connectionId);
}


/**
 * get the current connection status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.module_GetConnectionStatus = function(connectionId) {
  return internalGlue.internal_GetConnectionStatus(objectCache, connectionId);
}


/**
 * Get the device twin
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_GetTwin = function(connectionId) {
  return internalGlue.internal_GetTwin(objectCache, connectionId);
}


/**
 * call the given method on the given device
 *
 * connectionId String Id for the connection
 * deviceId String
 * methodInvokeParameters Object
 * returns Object
 **/
exports.module_InvokeDeviceMethod = function(connectionId,deviceId,methodInvokeParameters) {
  debug(`module_InvokeDeviceMethod called with ${connectionId}, ${deviceId}`);
  debug(JSON.stringify(methodInvokeParameters));
  return glueUtils.makePromise('module_InvokeDeviceMethod', function(callback) {
    var client = objectCache.getObject(connectionId);
    debug(`calling ModuleClient.invokeMethod`);
    client.invokeMethod(deviceId, methodInvokeParameters, function(err, result) {
      glueUtils.debugFunctionResult('client.invokeMethod', err);
      callback(err, result);
    });
  });
}


/**
 * call the given method on the given module
 *
 * connectionId String Id for the connection
 * deviceId String
 * moduleId String
 * methodInvokeParameters Object
 * returns Object
 **/
exports.module_InvokeModuleMethod = function(connectionId,deviceId,moduleId,methodInvokeParameters) {
  debug(`module_InvokeModuleMethod called with ${connectionId}, ${deviceId}, ${moduleId}`);
  debug(JSON.stringify(methodInvokeParameters));
  return glueUtils.makePromise('module_InvokeModuleMethod', function(callback) {
    var client = objectCache.getObject(connectionId);
    debug(`calling ModuleClient.invokeMethod`);
    client.invokeMethod(deviceId, moduleId, methodInvokeParameters, function(err, result) {
      glueUtils.debugFunctionResult('client.invokeMethod', err);
      callback(err, result);
    });
  });
}


/**
 * Updates the device twin
 *
 * connectionId String Id for the connection
 * props Object
 * no response value expected for this operation
 **/
exports.module_PatchTwin = function(connectionId,props) {
  return internalGlue.internal_PatchTwin(objectCache, connectionId, props);
}


/**
 * Reconnect the module
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.module_Reconnect = function(connectionId,forceRenewPassword) {
  return internalGlue.internal_Reconnect(objectCache, connectionId);
}


/**
 * Wait for a method call, verify the request, and return the response.
 * This is a workaround to deal with SDKs that only have method call operations that are sync.  This function responds to the method with the payload of this function, and then returns the method parameters.  Real-world implemenatations would never do this, but this is the only same way to write our test code right now (because the method handlers for C, Java, and probably Python all return the method response instead of supporting an async method call)
 *
 * connectionId String Id for the connection
 * methodName String name of the method to handle
 * requestAndResponse RoundtripMethodCallBody
 * no response value expected for this operation
 **/
exports.module_WaitForMethodAndReturnResponse = function(connectionId,methodName,requestAndResponse) {
  return internalGlue.internal_WaitForMethodAndReturnResponse(objectCache, connectionId, methodName, requestAndResponse);
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody Object
 * no response value expected for this operation
 **/
exports.module_SendEvent = function(connectionId,eventBody) {
  return internalGlue.internal_SendEvent(objectCache, connectionId, eventBody);
}


/**
 * Send an event to a module output
 *
 * connectionId String Id for the connection
 * outputName String
 * eventBody Object
 * no response value expected for this operation
 **/
exports.module_SendOutputEvent = function(connectionId,outputName,eventBody) {
  debug(`module_SendOutputEvent called with ${connectionId}, ${outputName}`);
  debug(eventBody);
  return glueUtils.makePromise('module_SendOutputEvent', function(callback) {
    var client = objectCache.getObject(connectionId)
    client.sendOutputEvent(outputName, new Message(JSON.stringify(eventBody.body)), function(err, result) {
      glueUtils.debugFunctionResult('client.sendOutputEvent', err);
      callback(err, result);
    });
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.module_WaitForConnectionStatusChange = function(connectionId) {
    return internalGlue.internal_WaitForConnectionStatusChange(objectCache, connectionId);
}


/**
 * Wait for the next desired property patch
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_WaitForDesiredPropertiesPatch = function(connectionId) {
    return internalGlue.internal_WaitForDesiredPropertiesPatch(objectCache, connectionId);
}


/**
 * Wait for a message on a module input
 *
 * connectionId String Id for the connection
 * inputName String
 * returns String
 **/
exports.module_WaitForInputMessage = function(connectionId,inputName) {
  debug(`module_WaitForInputMessage called with ${connectionId}, ${inputName}`);
  return glueUtils.makePromise('module_WaitForInputMessage', function(callback) {
    var client = objectCache.getObject(connectionId)
    var handler = function(receivedInputName, msg) {
      if (inputName === '*') {
        client.complete(msg, function(err) {
          glueUtils.debugFunctionResult('client.complete', err);
          callback(null, {
            inputName: receivedInputName,
            msg: {body: JSON.parse(msg.getBytes().toString('ascii'))}
          });
        });
      } else if (receivedInputName === inputName) {
        client.removeListener('inputMessage', handler);
        client.complete(msg, function(err) {
          glueUtils.debugFunctionResult('client.complete', err);
          callback(null, {body: JSON.parse(msg.getBytes().toString('ascii'))});
        });
      }
    };
    client.on('inputMessage', handler);
  });
}

