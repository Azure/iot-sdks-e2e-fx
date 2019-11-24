'use strict';
// Added in merge
/*jshint esversion: 6 */


/**
 * Connect to the azure IoT Hub as a module
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.module_Connect = function(transportType,connectionString,caCertificate) {
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
 * Connect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Connect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Connect to the azure IoT Hub as a module using the environment variables
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_ConnectFromEnvironment = function(transportType) {
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
 * Create a module client from a connection string
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.module_CreateFromConnectionString = function(transportType,connectionString,caCertificate) {
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
 * Create a module client using the EdgeHub environment
 *
 * transportType String Transport to use
 * returns connectResponse
 **/
exports.module_CreateFromEnvironment = function(transportType) {
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
 * Create a module client from X509 credentials
 *
 * transportType String Transport to use
 * x509 Object 
 * returns connectResponse
 **/
exports.module_CreateFromX509 = function(transportType,x509) {
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
 * Disonnect and destroy the module client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Destroy = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Disconnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Disonnect the module
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_Disconnect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Enable input messages
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableInputMessages = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Enable methods
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableMethods = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Enable module twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.module_EnableTwin = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * get the current connection status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.module_GetConnectionStatus = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * Get the device twin
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_GetTwin = function(connectionId) {
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
 * call the given method on the given device
 *
 * connectionId String Id for the connection
 * deviceId String 
 * methodInvokeParameters Object 
 * returns Object
 **/
exports.module_InvokeDeviceMethod = function(connectionId,deviceId,methodInvokeParameters) {
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
 * methodInvokeParameters Object 
 * returns Object
 **/
exports.module_InvokeModuleMethod = function(connectionId,deviceId,moduleId,methodInvokeParameters) {
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
 * Updates the device twin
 *
 * connectionId String Id for the connection
 * props Object 
 * no response value expected for this operation
 **/
exports.module_PatchTwin = function(connectionId,props) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Reconnect the module
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.module_Reconnect = function(connectionId,forceRenewPassword) {
  return new Promise(function(resolve, reject) {
    resolve();
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
exports.module_RoundtripMethodCall = function(connectionId,methodName,requestAndResponse) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody Object 
 * no response value expected for this operation
 **/
exports.module_SendEvent = function(connectionId,eventBody) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Send an event to a module output
 *
 * connectionId String Id for the connection
 * outputName String 
 * eventBody Object 
 * no response value expected for this operation
 **/
exports.module_SendOutputEvent = function(connectionId,outputName,eventBody) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * returns String
 **/
exports.module_WaitForConnectionStatusChange = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * Wait for the next desired property patch
 *
 * connectionId String Id for the connection
 * returns Object
 **/
exports.module_WaitForDesiredPropertiesPatch = function(connectionId) {
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
 * Wait for a message on a module input
 *
 * connectionId String Id for the connection
 * inputName String 
 * returns String
 **/
exports.module_WaitForInputMessage = function(connectionId,inputName) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
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
module.exports = require('../glue/glueUtils').replaceExports(module.exports, '../glue/moduleGlue.js')