// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');
var NamedObjectCache = require('./NamedObjectCache');

var Registry = require('azure-iothub').Registry;


/**
 * cache of objects.  Used to return object by name to the caller.
 */
var objectCache = new NamedObjectCache();

/**
 * Connect to registry
 * Connect to the Azure IoTHub registry.  More specifically, the SDK saves the connection string that is passed in for future use.
 *
 * connectionString String connection string
 * returns connectResponse
 **/
exports.registry_Connect = function(connectionString) {
  debug(`registry_Connect called`);
  return glueUtils.makePromise('registry_Connect', function(callback) {
    var registry = Registry.fromConnectionString(connectionString);
    var connectionId = objectCache.addObject('registry', registry);
    callback(null, {connectionId: connectionId});
  });
}


/**
 * Disconnect from the registry
 * Disconnects from the Azure IoTHub registry.  More specifically, closes all connections and cleans up all resources for the active connection
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.registry_Disconnect = function(connectionId) {
  debug(`registry_Disconnect called with ${connectionId}`);
  return glueUtils.makePromise('registry_Disconnect', function(callback) {
    var registry = objectCache.removeObject(connectionId);
    if (!registry) {
      debug(`${connectionId} already closed.`);
      callback();
    } else {
      debug(`Removed registry for ${connectionId}.`);
      callback();
    }
  });
}


/**
 * gets the device twin for the given deviceid
 *
 * connectionId String Id for the connection
 * deviceId String 
 * returns Object
 **/
exports.registry_GetDeviceTwin = function(connectionId,deviceId) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * gets the module twin for the given deviceid and moduleid
 *
 * connectionId String Id for the connection
 * deviceId String 
 * moduleId String 
 * returns Object
 **/
exports.registry_GetModuleTwin = function(connectionId,deviceId,moduleId) {
  debug(`registry_GetModuleTwin called with ${connectionId}, ${deviceId}, ${moduleId}`);
  return glueUtils.makePromise('registry_GetModuleTwin', function(callback) {
    var registry = objectCache.getObject(connectionId);
    debug(`calling Registry.getModuleTwin`);
    registry.getModuleTwin(deviceId, moduleId, function(err, result) {
      glueUtils.debugFunctionResult('registry.getModuleTwin', err);
      callback(err, result);
    });
  });
}


/**
 * update the device twin for the given deviceId
 *
 * connectionId String Id for the connection
 * deviceId String 
 * props Object 
 * no response value expected for this operation
 **/
exports.registry_PatchDeviceTwin = function(connectionId,deviceId,props) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * update the module twin for the given deviceId and moduleId
 *
 * connectionId String Id for the connection
 * deviceId String 
 * moduleId String 
 * props Object 
 * no response value expected for this operation
 **/
exports.registry_PatchModuleTwin = function(connectionId,deviceId,moduleId,props) {
  debug(`registry_PatchModuleTwin called with ${connectionId}, ${deviceId}, ${moduleId}`);
  debug(props);
  return glueUtils.makePromise('registry_PatchModuleTwin', function(callback) {
    var registry = objectCache.getObject(connectionId);
    debug(`calling Registry.updateModuleTwin`);
    registry.updateModuleTwin(deviceId, moduleId, props, '*', function(err, result) {
      glueUtils.debugFunctionResult('registry.updateModuleTwin', err);
      callback(err, result);
    });
  });
}

