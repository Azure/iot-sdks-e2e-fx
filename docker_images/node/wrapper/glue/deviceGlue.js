// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var Client = require('azure-iot-device').Client;
var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');
var NamedObjectCache = require('./NamedObjectCache');
var internalGlue = require('./internalGlue')

/**
 * cache of objects.  Used to return object by name to the caller.
 */
var objectCache = new NamedObjectCache();

/**
 * Connect to the azure IoT Hub as a device
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.device_Connect = function(transportType,connectionString,caCertificate) {
  debug(`device_Connect called with transport ${transportType}`);
  return glueUtils.makePromise('device_Connect', function(callback) {
    var client = Client.fromConnectionString(connectionString, glueUtils.transportFromType(transportType));
    glueUtils.setOptionalCert(client, caCertificate, function(err) {
      glueUtils.debugFunctionResult('glueUtils.setOptionalCert', err);
      if (err) {
        callback(err);
      } else {
        debug('calling client.open');
        client.open(function(err) {
          glueUtils.debugFunctionResult('client.open', err);
          if (err) {
            callback(err);
          } else {
            var connectionId = objectCache.addObject('DeviceClient', client);
            callback(null, {connectionId: connectionId});
          }
        });
      }
    });
  });
}


/**
 * Connect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Connect2 = function(connectionId) {
  return internalGlue.internal_Connect2(objectCache, connectionId);
}


/**
 * Create a device client from a connection string
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.device_CreateFromConnectionString = function(transportType,connectionString,caCertificate) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Create a device client from X509 credentials
 *
 * transportType String Transport to use
 * x509 Object 
 * returns connectResponse
 **/
exports.device_CreateFromX509 = function(transportType,x509) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disconnect and destroy the device client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Destroy = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * Disconnect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Disconnect = function(connectionId) {
    return internalGlue.internal_Disconnect(objectCache, connectionId);
}


/**
 * Disconnect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Disconnect2 = function(connectionId) {
  return internalGlue.internal_Disconnect(objectCache, connectionId);
}


/**
 * Enable c2d messages
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_EnableC2dMessages = function(connectionId) {
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
exports.device_EnableMethods = function(connectionId) {
  return internalGlue.internal_EnableMethods(objectCache, connectionId);
}


/**
 * Enable device twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_EnableTwin = function(connectionId) {
  return internalGlue.internal_EnableTwin(objectCache, connectionId);
}


/**
 * get the current connection status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.device_GetConnectionStatus = function(connectionId) {
  return internalGlue.internal_GetConnectionStatus(objectCache, connectionId);
}


/**
 * Get the device twin
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.device_GetTwin = function(connectionId) {
  return internalGlue.internal_GetTwin(objectCache, connectionId);
}


/**
 * Updates the device twin
 *
 * connectionId String Id for the connection
 * props Object 
 * no response value expected for this operation
 **/
exports.device_PatchTwin = function(connectionId,props) {
  return internalGlue.internal_PatchTwin(objectCache, connectionId, props);
}


/**
 * Reconnect the device
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.device_Reconnect = function(connectionId,forceRenewPassword) {
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
exports.device_RoundtripMethodCall = function(connectionId,methodName,requestAndResponse) {
  return internalGlue.internal_RoundtripMethodCall(objectCache, connectionId, methodName, requestAndResponse);
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody Object 
 * no response value expected for this operation
 **/
exports.device_SendEvent = function(connectionId,eventBody) {
  return internalGlue.internal_SendEvent(objectCache, eventBody);
}


/**
 * Wait for a c2d message
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.device_WaitForC2dMessage = function(connectionId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.device_WaitForConnectionStatusChange = function(connectionId) {
  return internalGlue.internal_WaitForConnectionStatusChange(objectCache, connectionId);
}


/**
 * Wait for the next desired property patch
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.device_WaitForDesiredPropertiesPatch = function(connectionId) {
  return internalGlue.internal_WaitForDesiredPropertiesPatch(objectCache, connectionId);
}

