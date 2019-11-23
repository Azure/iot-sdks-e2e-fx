'use strict';
// Added in merge
/*jshint esversion: 6 */


/**
 * verify that the clients have cleaned themselves up completely
 *
 * no response value expected for this operation
 **/
exports.wrapper_Cleanup = function() {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Get capabilities for this test wrapper
 *
 * returns Object
 **/
exports.wrapper_GetCapabilities = function() {
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
 * msg Object 
 * no response value expected for this operation
 **/
exports.wrapper_LogMessage = function(msg) {
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
exports.wrapper_SendCommand = function(cmd) {
  return new Promise(function(resolve, reject) {
    resolve();
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
    resolve();
  });
}

// Added in merge
// WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
//
// When updating this file, make sure the code below ends up in the new file.  This is how we
// avoid changing the codegen code.  The real implementations are in the *Glue.js files, and we leave the
// codegen stubs in here.  We replace all the codegen implementations with our new implementations
// and then make sure we've replaced them all before exporting.
//
// WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING
module.exports = require('../glue/glueUtils').replaceExports(module.exports, '../glue/wrapperGlue.js')

