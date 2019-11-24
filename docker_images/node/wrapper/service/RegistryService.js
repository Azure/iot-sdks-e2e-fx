'use strict';


/**
 * Connect to registry
 * Connect to the Azure IoTHub registry.  More specifically, the SDK saves the connection string that is passed in for future use.
 *
 * connectionString String connection string
 * returns connectResponse
 **/
exports.registry_Connect = function(connectionString) {
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
 * Disconnect from the registry
 * Disconnects from the Azure IoTHub registry.  More specifically, closes all connections and cleans up all resources for the active connection
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.registry_Disconnect = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
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
 * gets the module twin for the given deviceid and moduleid
 *
 * connectionId String Id for the connection
 * deviceId String 
 * moduleId String 
 * returns Object
 **/
exports.registry_GetModuleTwin = function(connectionId,deviceId,moduleId) {
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
 * update the device twin for the given deviceId
 *
 * connectionId String Id for the connection
 * deviceId String 
 * props Object 
 * no response value expected for this operation
 **/
exports.registry_PatchDeviceTwin = function(connectionId,deviceId,props) {
  return new Promise(function(resolve, reject) {
    resolve();
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
  return new Promise(function(resolve, reject) {
    resolve();
  });
}

