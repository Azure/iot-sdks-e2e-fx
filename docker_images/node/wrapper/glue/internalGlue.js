// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var Message = require('azure-iot-device').Message;
var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');

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
var getModuleOrDeviceTwin = function(objectCache, connectionId, callback) {
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
 * Connect the client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_Connect2 = function(objectCache, connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disonnect and destroy the client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_Destroy = function(objectCache, connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disconnect the client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_Disconnect = function(objectCache, connectionId) {
  debug(`internal_Disconnect called with ${connectionId}`);
  return glueUtils.makePromise('internal_Disconnect', function(callback) {
    var client = objectCache.removeObject(connectionId);
    if (!client) {
      debug(`${connectionId} already closed.`);
      callback();
    } else {
      debug('calling client.close');
      client.close(function(err) {
        glueUtils.debugFunctionResult('client.close', err);
        callback(err);
      });
    }
  });
}


/**
 * Disonnect the client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_Disconnect2 = function(objectCache, connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Enable methods
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_EnableMethods = function(objectCache, connectionId) {
  debug(`internal_EnableMethods called with ${connectionId}`);
  return glueUtils.makePromise('internal_EnableMethods', function(callback) {
    var client = objectCache.getObject(connectionId)
    client._enableMethods(function(err) {
      glueUtils.debugFunctionResult('client._enableMethods', err);
      callback(err);
    });
  });
}


/**
 * Enable twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.internal_EnableTwin = function(objectCache, connectionId) {
  debug(`internal_EnableTwin called with ${connectionId}`);
  return glueUtils.makePromise('internal_EnableTwin', function(callback) {
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
exports.internal_GetConnectionStatus = function(objectCache, connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Get the twin
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.internal_GetTwin = function(objectCache, connectionId) {
  debug(`internal_GetTwin called with ${connectionId}`);
  return glueUtils.makePromise('internal_GetTwin', function(callback) {
    getModuleOrDeviceTwin(objectCache, connectionId, function(err, twin) {
      glueUtils.debugFunctionResult('getModuleOrDeviceTwin', err);
      if (err) {
        callback(err);
      } else {
        callback(null, JSON.parse(JSON.stringify(twin.properties)));
      }
    });
  });
}


/**
 * Updates the twin
 *
 * connectionId String Id for the connection
 * props Object
 * no response value expected for this operation
 **/
exports.internal_PatchTwin = function(objectCache, connectionId,props) {
  debug(`internal_PatchTwin for ${connectionId} called with ${JSON.stringify(props)}`);
  return glueUtils.makePromise('internal_PatchTwin', function(callback) {
    getModuleOrDeviceTwin(objectCache, connectionId, function(err, twin) {
      glueUtils.debugFunctionResult('getModuleOrDeviceTwin', err);
      if (err) {
        callback(err);
      } else {
        try {
          twin.properties.reported.update(props["reported"], function(err) {
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
 * Reconnect the client
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.internal_Reconnect = function(objectCache, connectionId,forceRenewPassword) {
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
exports.internal_WaitForMethodAndReturnResponse = function(objectCache, connectionId,methodName,requestAndResponse) {
  debug(`internal_WaitForMethodAndReturnResponse called with ${connectionId}, ${methodName}`);
  debug(JSON.stringify(requestAndResponse, null, 2));
  return glueUtils.makePromise('internal_RoundtripMethodCall', function(callback) {
    var client = objectCache.getObject(connectionId);
    var onMethod = client.onMethod || client.onDeviceMethod;
    onMethod.bind(client)(methodName, function(request, response) {
      debug(`function ${methodName} invoked from service`);
      debug(JSON.stringify(request, null, 2));
      // Java stringifies the payload.  This is why we have the second comparison.
      if ((JSON.stringify(request.payload) !== JSON.stringify(requestAndResponse.requestPayload.payload)) &&
          (request.payload !== JSON.stringify(requestAndResponse.requestPayload.payload))) {
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
exports.internal_SendEvent = function(objectCache, connectionId,eventBody) {
  debug(`internal_SendEvent called with ${connectionId}`);
  debug(eventBody);
  return glueUtils.makePromise('internal_SendEvent', function(callback) {
    var client = objectCache.getObject(connectionId)
    client.sendEvent(new Message(JSON.stringify(eventBody.body)), function(err) {
      glueUtils.debugFunctionResult('client.sendEvent', err);
      callback(err);
    })
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.internal_WaitForConnectionStatusChange = function(objectCache, connectionId) {
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
exports.internal_WaitForDesiredPropertiesPatch = function(objectCache, connectionId) {
  debug(`internal_WaitForDesiredPropertiesPatch called with ${connectionId}`);
  return glueUtils.makePromise('internal_WaitForDesiredPropertiesPatch', function(callback) {
    getModuleOrDeviceTwin(objectCache, connectionId, function(err, twin) {
      if (err) {
        callback(err);
      } else {
        callbackForSecondEventOnly(twin, 'properties.desired', function(delta) {
          callback(null, {'desired': delta});
        });
      }
    });
  });
}


