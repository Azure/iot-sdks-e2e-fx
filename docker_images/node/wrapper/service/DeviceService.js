'use strict';
// Added in merge
/*jshint esversion: 6 */


/**
 * Connect to the azure IoT Hub as a device
 *
 * transportType String Transport to use
 * connectionString String connection string
 * caCertificate Certificate  (optional)
 * returns connectResponse
 **/
exports.device_Connect = function(transportType,connectionString,caCertificate) {
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
 * Connect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Connect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
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
 * Create a device client from a symmetric key
 *
 * transportType String Transport to use
 * deviceId String 
 * hostname String name of the host to connect to
 * symmetricKey String key to use for connection
 * returns connectResponse
 **/
exports.device_CreateFromSymmetricKey = function(transportType,deviceId,hostname,symmetricKey) {
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
 * Create a device client from X509 credentials
 *
 * transportType String Transport to use
 * x509 Object 
 * returns connectResponse
 **/
exports.device_CreateFromX509 = function(transportType,x509) {
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
 * Disconnect and destroy the device client
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Destroy = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Disconnect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Disconnect = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Disconnect the device
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_Disconnect2 = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Enable c2d messages
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_EnableC2dMessages = function(connectionId) {
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
exports.device_EnableMethods = function(connectionId) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Enable device twins
 *
 * connectionId String Id for the connection
 * no response value expected for this operation
 **/
exports.device_EnableTwin = function(connectionId) {
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
exports.device_GetConnectionStatus = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = "";
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * Get storage info for uploading into blob storage
 *
 * connectionId String Id for the connection
 * blobName String name of blob for blob upload
 * returns blobStorageInfo
 **/
exports.device_GetStorageInfoForBlob = function(connectionId,blobName) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = {
  "blobName" : "blobName",
  "sasToken" : "sasToken",
  "hostName" : "hostName",
  "containerName" : "containerName",
  "correlationId" : "correlationId"
};
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
 * returns twin
 **/
exports.device_GetTwin = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = {
  "desired" : "{}",
  "reported" : "{}"
};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
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
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Updates the device twin
 *
 * connectionId String Id for the connection
 * twin Twin 
 * no response value expected for this operation
 **/
exports.device_PatchTwin = function(connectionId,twin) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Reconnect the device
 *
 * connectionId String Id for the connection
 * forceRenewPassword Boolean True to force SAS renewal (optional)
 * no response value expected for this operation
 **/
exports.device_Reconnect = function(connectionId,forceRenewPassword) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Send an event
 *
 * connectionId String Id for the connection
 * eventBody EventBody 
 * no response value expected for this operation
 **/
exports.device_SendEvent = function(connectionId,eventBody) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Wait for a c2d message
 *
 * connectionId String Id for the connection
 * returns eventBody
 **/
exports.device_WaitForC2dMessage = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = {
  "horton_flags" : "{}",
  "attributes" : "{}",
  "body" : "{}"
};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * wait for the current connection status to change and return the changed status
 *
 * connectionId String Id for the connection
 * connectionStatus String Desired connection status
 * returns String
 **/
exports.device_WaitForConnectionStatusChange = function(connectionId,connectionStatus) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = "";
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
 * returns twin
 **/
exports.device_WaitForDesiredPropertiesPatch = function(connectionId) {
  return new Promise(function(resolve, reject) {
    var examples = {};
    examples['application/json'] = {
  "desired" : "{}",
  "reported" : "{}"
};
    if (Object.keys(examples).length > 0) {
      resolve(examples[Object.keys(examples)[0]]);
    } else {
      resolve();
    }
  });
}


/**
 * Wait for a method call, verify the request, and return the response.
 * This is a workaround to deal with SDKs that only have method call operations that are sync.  This function responds to the method with the payload of this function, and then returns the method parameters.  Real-world implemenatations would never do this, but this is the only same way to write our test code right now (because the method handlers for C, Java, and probably Python all return the method response instead of supporting an async method call)
 *
 * connectionId String Id for the connection
 * methodName String name of the method to handle
 * requestAndResponse MethodRequestAndResponse 
 * no response value expected for this operation
 **/
exports.device_WaitForMethodAndReturnResponse = function(connectionId,methodName,requestAndResponse) {
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
module.exports = require('../glue/glueUtils').replaceExports(module.exports, '../glue/deviceGlue.js')

