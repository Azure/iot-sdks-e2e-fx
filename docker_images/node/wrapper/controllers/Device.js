'use strict';

var utils = require('../utils/writer.js');
var Device = require('../service/DeviceService');

module.exports.device_Connect = function device_Connect (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var connectionString = req.swagger.params['connectionString'].value;
  var caCertificate = req.swagger.params['caCertificate'].value;
  Device.device_Connect(transportType,connectionString,caCertificate)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_Connect2 = function device_Connect2 (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_Connect2(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_CreateFromConnectionString = function device_CreateFromConnectionString (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var connectionString = req.swagger.params['connectionString'].value;
  var caCertificate = req.swagger.params['caCertificate'].value;
  Device.device_CreateFromConnectionString(transportType,connectionString,caCertificate)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_CreateFromSymmetricKey = function device_CreateFromSymmetricKey (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var deviceId = req.swagger.params['deviceId'].value;
  var hostname = req.swagger.params['hostname'].value;
  var symmetricKey = req.swagger.params['symmetricKey'].value;
  Device.device_CreateFromSymmetricKey(transportType,deviceId,hostname,symmetricKey)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_CreateFromX509 = function device_CreateFromX509 (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var x509 = req.swagger.params['X509'].value;
  Device.device_CreateFromX509(transportType,x509)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_Destroy = function device_Destroy (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_Destroy(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_Disconnect = function device_Disconnect (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_Disconnect(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_Disconnect2 = function device_Disconnect2 (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_Disconnect2(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_EnableC2dMessages = function device_EnableC2dMessages (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_EnableC2dMessages(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_EnableMethods = function device_EnableMethods (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_EnableMethods(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_EnableTwin = function device_EnableTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_EnableTwin(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_GetConnectionStatus = function device_GetConnectionStatus (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_GetConnectionStatus(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_GetStorageInfoForBlob = function device_GetStorageInfoForBlob (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var blobName = req.swagger.params['blobName'].value;
  Device.device_GetStorageInfoForBlob(connectionId,blobName)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_GetTwin = function device_GetTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_GetTwin(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_NotifyBlobUploadStatus = function device_NotifyBlobUploadStatus (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var correlationId = req.swagger.params['correlationId'].value;
  var isSuccess = req.swagger.params['isSuccess'].value;
  var statusCode = req.swagger.params['statusCode'].value;
  var statusDescription = req.swagger.params['statusDescription'].value;
  Device.device_NotifyBlobUploadStatus(connectionId,correlationId,isSuccess,statusCode,statusDescription)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_PatchTwin = function device_PatchTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var twin = req.swagger.params['twin'].value;
  Device.device_PatchTwin(connectionId,twin)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_Reconnect = function device_Reconnect (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var forceRenewPassword = req.swagger.params['forceRenewPassword'].value;
  Device.device_Reconnect(connectionId,forceRenewPassword)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_SendEvent = function device_SendEvent (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var eventBody = req.swagger.params['eventBody'].value;
  Device.device_SendEvent(connectionId,eventBody)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_WaitForC2dMessage = function device_WaitForC2dMessage (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_WaitForC2dMessage(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_WaitForConnectionStatusChange = function device_WaitForConnectionStatusChange (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var connectionStatus = req.swagger.params['connectionStatus'].value;
  Device.device_WaitForConnectionStatusChange(connectionId,connectionStatus)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_WaitForDesiredPropertiesPatch = function device_WaitForDesiredPropertiesPatch (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Device.device_WaitForDesiredPropertiesPatch(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.device_WaitForMethodAndReturnResponse = function device_WaitForMethodAndReturnResponse (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var methodName = req.swagger.params['methodName'].value;
  var requestAndResponse = req.swagger.params['requestAndResponse'].value;
  Device.device_WaitForMethodAndReturnResponse(connectionId,methodName,requestAndResponse)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
