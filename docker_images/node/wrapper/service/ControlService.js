'use strict';
// Added in merge
/*jshint esversion: 6 */


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
 * Get statistics about the operation of the test wrapper
 *
 * returns Object
 **/
exports.control_GetWrapperStats = function() {
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


// Added in merge 
//
// When updating this file, make sure the code below ends up in the new file.  This is how we
// avoid changing the codegen code.  The real implementations are in the *Glue.js files, and we leave the
// codegen stubs in here.  We replace all the codegen implementations with our new implementations
// and then make sure we've replaced them all before exporting.
//
// WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
module.exports = require('../glue/glueUtils').replaceExports(module.exports, '../glue/controlGlue.js')

