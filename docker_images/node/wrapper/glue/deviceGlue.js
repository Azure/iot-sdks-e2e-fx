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
  return glueUtils.returnNotImpl();
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
  return internalGlue.internal_CreateFromConnectionString(objectCache, Client, transportType, connectionString, caCertificate);
}

/**
 * Create a device client from X509 credentials
 *
 * transportType String Transport to use
 * x509 Object 
 * returns connectResponse
 **/
exports.device_CreateFromX509 = function(transportType,x509) {
  return glueUtils.returnNotImpl();
}


/**
 * Disconnect and destroy the device client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Destroy = function(connectionId) {
  return internalGlue.internal_Destroy(objectCache, connectionId);
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
  return internalGlue.internal_Disconnect2(objectCache, connectionId);
}


/**
 * Enable c2d messages
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_EnableC2dMessages = function(connectionId) {
  debug(`device_EnableC2dMessages called with ${connectionId}`);
  return glueUtils.makePromise('device_EnableC2dMessages', function(callback) {
    var client = objectCache.getObject(connectionId)
    client._enableC2D(function(err) {
      glueUtils.debugFunctionResult('client._enableC2D', err);
      callback(err);
    });
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
exports.device_WaitForMethodAndReturnResponse = function(connectionId,methodName,requestAndResponse) {
  return internalGlue.internal_WaitForMethodAndReturnResponse(objectCache, connectionId, methodName, requestAndResponse);
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody Object 
 * no response value expected for this operation
 **/
exports.device_SendEvent = function(connectionId,eventBody) {
  return internalGlue.internal_SendEvent(objectCache, connectionId, eventBody);
}


/**
 * Wait for a c2d message
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.device_WaitForC2dMessage = function(connectionId) {
  debug(`device_WaitForC2dMessage called with ${connectionId}`);
  return glueUtils.makePromise('device_WaitForC2dMessage', function(callback) {
    var client = objectCache.getObject(connectionId)
    var handler = function(msg) {
      client.complete(msg, function(err) {
        debug(`received $msg`);
        glueUtils.debugFunctionResult('client.complete', err);
        callback(null, {
          body: JSON.parse(msg.getBytes().toString('ascii'))
        });
      });
      client.removeListener('message', handler);
    }
    client.on('message', handler);
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.device_WaitForConnectionStatusChange = function(connectionId, connectionStatus) {
  return internalGlue.internal_WaitForConnectionStatusChange(objectCache, connectionId, connectionStatus);
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

/**
 * Get storage info for uploading into blob storage
 *
 * connectionId String Id for the connection
 * blobName String name of blob for blob upload
 * returns blobStorageInfo
 **/
exports.device_GetStorageInfoForBlob = function(connectionId,blobName) {
  return internalGlue.internal_GetStorageInfoForBlob(objectCache, connectionId, blobName);
}

/**
 * notify iothub about blob upload status
 *
 * connectionId String Id for the connection
 * correlationId String correlation id for blob upload
 * isSuccess Boolean True if blob upload was successful
 * statusCode String status code for blob upload
 * statusDescription String human readable descripton of the status for blob upload
 * no response value expected for this operation
 **/
exports.device_NotifyBlobUploadStatus = function(connectionId,correlationId,isSuccess,statusCode,statusDescription) {
  return internalGlue.internal_NotifyBlobUploadStatus(objectCache, connectionId, correlationId, isSuccess, statusCode, statusDescription);
}


