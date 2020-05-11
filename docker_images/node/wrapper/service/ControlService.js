'use strict';


/**
 * verify that the clients have cleaned themselves up completely
 *
 * no response value expected for this operation
 **/
exports.control_Cleanup = function() {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Get capabilities for the objects in this server
 *
 * returns Object
 **/
exports.control_GetCapabilities = function() {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = "{}";
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * log a message to output
 *
 * logMessage LogMessage 
 * no response value expected for this operation
 **/
exports.control_LogMessage = function(logMessage) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * send an arbitrary command
 *
 * cmd String command string
 * no response value expected for this operation
 **/
exports.control_SendCommand = function(cmd) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * set flags for the objects in this server to use
 *
 * flags Object 
 * no response value expected for this operation
 **/
exports.control_SetFlags = function(flags) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}

