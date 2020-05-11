'use strict';


/**
 * Connect to service
 * Connect to the Azure IoTHub service.  More specifically, the SDK saves the connection string that is passed in for future use.
 *
 * connectionString String connection string
 * returns connectResponse
 **/
exports.service_Connect = function(connectionString) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = {
  "connectionId" : "connectionId"
};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * Disconnect from the service
 * Disconnects from the Azure IoTHub service.  More specifically, closes all connections and cleans up all resources for the active connection
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.service_Disconnect = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * call the given method on the given device
 *
 * connectionId String Id for the connection
 * deviceId String 
 * methodInvokeParameters MethodInvoke 
 * returns Object
 **/
exports.service_InvokeDeviceMethod = function(connectionId,deviceId,methodInvokeParameters) {
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
 * call the given method on the given module
 *
 * connectionId String Id for the connection
 * deviceId String 
 * moduleId String 
 * methodInvokeParameters MethodInvoke 
 * returns Object
 **/
exports.service_InvokeModuleMethod = function(connectionId,deviceId,moduleId,methodInvokeParameters) {
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
 * Send a c2d message
 *
 * connectionId String Id for the connection
 * deviceId String 
 * eventBody EventBody 
 * no response value expected for this operation
 **/
exports.service_SendC2d = function(connectionId,deviceId,eventBody) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}

