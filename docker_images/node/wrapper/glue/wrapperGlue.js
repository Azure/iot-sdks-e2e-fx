// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
/*jshint esversion: 6 */

var async = require('async');
var debug = require('debug')('azure-iot-e2e:node')
var glueUtils = require('./glueUtils');
var moduleGlue = require('./moduleGlue');
var registryGlue = require('./registryGlue');
var serviceGlue = require('./serviceGlue');
var deviceGlue = require('./deviceGlue');

/**
 * Cleanup an individual glue module
 */
var cleanupGlueModule = function(mod, callback) {
  var remainingObjects = mod._objectCache.getMap();

  async.forEachSeries(Object.keys(remainingObjects), function(objectId, callback) {
    if (objectId.indexOf('response_') === 0) {
      // not a failure
      debug(`removing dangling object ${objectId}`);
      mod._objectCache.removeObject(objectId);
      callback();
    } else {
      debug('Cleaning up ' + objectId);
      var obj = mod._objectCache.removeObject(objectId);
      var closeFunc = obj.close || obj.closeClient;
      if (closeFunc) {
        try {
          closeFunc.bind(obj)(function(err) {
            if (err) {
              debug('ignoring close error: ' + err.message);
            }
            callback();
          })
        } catch (e) {
          debug('ignoring close exception: ' + e.message);
          callback();
        }
      } else {
        callback();
      }
    }
  }, callback);
};

/**
 * verify that the clients have cleaned themselves up completely
 *
 * no response value expected for this operation
 **/
exports.wrapper_Cleanup = function() {
  debug('wrapper_Cleanup called')
  return glueUtils.makePromise('wrapper_Cleanup', function(callback) {
    var objectsToClean = [
      moduleGlue,
      serviceGlue,
      registryGlue,
      deviceGlue
    ];
    async.forEachSeries(objectsToClean, cleanupGlueModule, callback);
  });
}


/**
 * Get capabilities for this test wrapper
 *
 * returns Object
 **/
exports.wrapper_GetCapabilities = function() {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * log a message to output
 *
 * msg Object 
 * no response value expected for this operation
 **/
exports.wrapper_LogMessage = function(msg) {
  return new Promise(function(resolve, reject) {
    if (msg.message) {
      debug(msg.message);
    } else {
      debug(msg);
    }
    resolve();
  });
}


/**
 * send an arbitrary command
 *
 * cmd String command string
 * no response value expected for this operation
 **/
exports.wrapper_SendCommand = function(cmd) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}


/**
 * set flags for the wrapper to use
 *
 * flags Object 
 * no response value expected for this operation
 **/
exports.wrapper_SetFlags = function(flags) {
  return new Promise(function(resolve, reject) {
    glueUtils.returnFailure(reject);
  });
}

