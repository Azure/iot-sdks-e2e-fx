// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var ModuleClient = require('azure-iot-device').ModuleClient;
var Message = require('azure-iot-device').Message;
var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');
var NamedObjectCache = require('./NamedObjectCache');

/**
 * cache of objects.  Used to return object by name to the caller.
 */
var objectCache = new NamedObjectCache();

/**
 * Create an event handler which calls the callback for the second event only.  Used
 * like EventEmitter.Once(), only it returns the second event and then removes itself.
 * This is needed for 'properties.desired' events because the first event comes when
 * registering for the hander, but in many cases, we want the second event which is
 * an actual delta.
 *
 * @param {Object} object     EventEmitter object for the event that we're registering for
 * @param {string} eventName  Name of the event that we're registering for
 * @param {function} cb       Callback to call when the second event is received.
 */
var callbackForSecondEventOnly = function(object, eventName, cb) {
  var alreadyReceivedFirstEvent = false;
  var handler = function(x) {
    if (alreadyReceivedFirstEvent) {
      object.removeListener(eventName, handler);
      cb(x);
    } else {
      alreadyReceivedFirstEvent = true;
    }
  }
  object.on(eventName, handler);
}

/**
 * Helper function which either creates a Twin or returns a Twin for the given connection
 * if it already exists.
 *
 * @param {string} connectionId   Connection to get the twin for
 * @param {function} callback     callback used to return the Twin object
 */
var getModuleOrDeviceTwin = function(connectionId, callback) {
  var client = objectCache.getObject(connectionId);
  // cheat: use internal member.  We should really call getTwin the first time
  // and cache the value in this code rather than relying on internal implementations.
  if (client._twin) {
    callback(null, client._twin);
  } else {
    client.getTwin(callback);
  }
}


/**
 * Connect to the azure IoT Hub as a module
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.module_Connect = function(transportType,connectionString,caCertificate) {
  debug(`module_Connect called`);
  return glueUtils.makePromise('module_Connect', function(callback) {
    var client = ModuleClient.fromConnectionString(connectionString, glueUtils.transportFromType(transportType));
    var connectionId = objectCache.addObject('moduleClient', client);
    glueUtils.setOptionalCert(client, caCertificate, function(err) {
      glueUtils.debugFunctionResult('glueUtils.setOptionalCert', err);
      if (err) {
        callback(err);
      } else {
        debug('calling moduleClient.open');
        client.open(function(err) {
          glueUtils.debugFunctionResult('client.open', err);
          if (err) {
            objectCache.removeObject(connectionId);
            callback(err);
          } else {
            callback(null, {connectionId: connectionId});
          }
        });
      }
    });
  });
}


/**
 * Connect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Connect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Connect to the azure IoT Hub as a module using the environment variables
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_ConnectFromEnvironment = function(transportType) {
  debug(`module_ConnectFromEnvironment called`);

  return glueUtils.makePromise('module_ConnectFromEnvironment', function(callback) {
    ModuleClient.fromEnvironment(glueUtils.transportFromType(transportType), function(err, client) {
      glueUtils.debugFunctionResult('ModuleClient.fromEnvironment', err);
      if (err) {
        callback(err);
      } else {
        debug('calling moduleClient.open');
        client.open(function(err) {
          glueUtils.debugFunctionResult('client.open', err);
          if (err) {
            callback(err);
          } else {
            var connectionId = objectCache.addObject('moduleClient', client);
            callback(null, {connectionId: connectionId});
          }
        });
      }
    });
  });
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
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Create a module client using the EdgeHub environment
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_CreateFromEnvironment = function(transportType) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
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
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disonnect and destroy the module client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Destroy = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disconnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect = function(connectionId) {
  debug(`module_Disconnect called with ${connectionId}`);
  return glueUtils.makePromise('module_Disconnect', function(callback) {
    var client = objectCache.removeObject(connectionId);
    if (!client) {
      debug(`${connectionId} already closed.`);
      callback();
    } else {
      debug('calling ModuleClient.close');
      client.close(function(err) {
        glueUtils.debugFunctionResult('client.close', err);
        callback(err);
      });
    }
  });
}


/**
 * Disonnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
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
  debug(`module_EnableMethods called with ${connectionId}`);
  return glueUtils.makePromise('module_EnableMethods', function(callback) {
    var client = objectCache.getObject(connectionId)
    client._enableMethods(function(err) {
      glueUtils.debugFunctionResult('client._enableMethods', err);
      callback(err);
    });
  });
}


/**
 * Enable module twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableTwin = function(connectionId) {
  debug(`module_EnableTwin called with ${connectionId}`);
  return glueUtils.makePromise('module_EnableTwin', function(callback) {
    var client = objectCache.getObject(connectionId)
    client.getTwin(function(err) {
      glueUtils.debugFunctionResult('client.getTwin', err);
      callback(err);
    });
  });
}


/**
 * get the current connection status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.module_GetConnectionStatus = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Get the device twin
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_GetTwin = function(connectionId) {
  debug(`module_GetTwin called with ${connectionId}`);
  return glueUtils.makePromise('module_GetTwin', function(callback) {
    getModuleOrDeviceTwin(connectionId, function(err, twin) {
      glueUtils.debugFunctionResult('getModuleOrDeviceTwin', err);
      if (err) {
        callback(err);
      } else {
        callback(null, {properties: JSON.parse(JSON.stringify(twin.properties))});
      }
    });
  });
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
  debug(`module_PatchTwin for ${connectionId} called with ${JSON.stringify(props)}`);
  return glueUtils.makePromise('module_PatchTwin', function(callback) {
    getModuleOrDeviceTwin(connectionId, function(err, twin) {
      glueUtils.debugFunctionResult('getModuleOrDeviceTwin', err);
      if (err) {
        callback(err);
      } else {
        try {
          twin.properties.reported.update(props, function(err) {
            glueUtils.debugFunctionResult('twin.properties.reported.update', err);
            if (err) {
              callback(err);
            } else {
              callback();
            }
          });
        } catch (e) {
          callback(e);
        }
      }
    });
  });
}


/**
 * Reconnect the module
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.module_Reconnect = function(connectionId,forceRenewPassword) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
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
exports.module_RoundtripMethodCall = function(connectionId,methodName,requestAndResponse) {
  debug(`module_RoundtripMethodCall called with ${connectionId}, ${methodName}`);
  debug(JSON.stringify(requestAndResponse, null, 2));
  return glueUtils.makePromise('module_RoundtripMethodCall', function(callback) {
    var client = objectCache.getObject(connectionId);
    client.onMethod(methodName, function(request, response) {
      debug(`function ${methodName} invoked from service`);
      debug(JSON.stringify(request, null, 2));
      if (JSON.stringify(request.payload) !== JSON.stringify(requestAndResponse.requestPayload.payload)) {
        debug('payload expected:' + JSON.stringify(requestAndResponse.requestPayload.payload));
        debug('payload received:' + JSON.stringify(request.payload));
        callback(new Error('request payload did not arrive as expected'))
      } else {
        debug('payload received as expected');
        response.send(requestAndResponse.statusCode, requestAndResponse.responsePayload, function(err) {
          debug('response sent');
          if (err) {
            callback(err);
          } else {
            callback(null, requestAndResponse.responsePayload);
          }
        });
      }
    });
  });
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody Object 
 * no response value expected for this operation
 **/
exports.module_SendEvent = function(connectionId,eventBody) {
  debug(`module_SendEvent called with ${connectionId}`);
  debug(eventBody);
  return glueUtils.makePromise('module_SendEvent', function(callback) {
    var client = objectCache.getObject(connectionId)
    client.sendEvent(new Message(eventBody), function(err) {
      glueUtils.debugFunctionResult('client.sendEvent', err);
      callback(err);
    })
  });
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
    client.sendOutputEvent(outputName, new Message(eventBody), function(err, result) {
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
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Wait for the next desired property patch
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_WaitForDesiredPropertiesPatch = function(connectionId) {
  debug(`module_WaitForDesiredPropertiesPatch called with ${connectionId}`);
  return glueUtils.makePromise('module_WaitForDesiredPropertiesPatch', function(callback) {
    getModuleOrDeviceTwin(connectionId, function(err, twin) {
      if (err) {
        callback(err);
      } else {
        callbackForSecondEventOnly(twin, 'properties.desired', function(delta) {
          callback(null, delta);
        });
      }
    });
  });
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
            msg: msg.getBytes().toString('ascii')
          });
        });
      } else if (receivedInputName === inputName) {
        client.removeListener('inputMessage', handler);
        client.complete(msg, function(err) {
          glueUtils.debugFunctionResult('client.complete', err);
          callback(null, msg.getBytes().toString('ascii'));
        });
      }
    };
    client.on('inputMessage', handler);
  });
}

