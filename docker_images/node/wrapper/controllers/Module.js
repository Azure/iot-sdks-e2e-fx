'use strict';

var utils = require('../utils/writer.js');
var Module = require('../service/ModuleService');

module.exports.module_Connect = function module_Connect (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var connectionString = req.swagger.params['connectionString'].value;
  var caCertificate = req.swagger.params['caCertificate'].value;
  Module.module_Connect(transportType,connectionString,caCertificate)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_Connect2 = function module_Connect2 (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_Connect2(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_ConnectFromEnvironment = function module_ConnectFromEnvironment (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  Module.module_ConnectFromEnvironment(transportType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_CreateFromConnectionString = function module_CreateFromConnectionString (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var connectionString = req.swagger.params['connectionString'].value;
  var caCertificate = req.swagger.params['caCertificate'].value;
  Module.module_CreateFromConnectionString(transportType,connectionString,caCertificate)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_CreateFromEnvironment = function module_CreateFromEnvironment (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  Module.module_CreateFromEnvironment(transportType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_CreateFromX509 = function module_CreateFromX509 (req, res, next) {
  var transportType = req.swagger.params['transportType'].value;
  var x509 = req.swagger.params['X509'].value;
  Module.module_CreateFromX509(transportType,x509)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_Destroy = function module_Destroy (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_Destroy(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_Disconnect = function module_Disconnect (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_Disconnect(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_Disconnect2 = function module_Disconnect2 (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_Disconnect2(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_EnableInputMessages = function module_EnableInputMessages (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_EnableInputMessages(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_EnableMethods = function module_EnableMethods (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_EnableMethods(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_EnableTwin = function module_EnableTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_EnableTwin(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_GetConnectionStatus = function module_GetConnectionStatus (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_GetConnectionStatus(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_GetTwin = function module_GetTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_GetTwin(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_InvokeDeviceMethod = function module_InvokeDeviceMethod (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var deviceId = req.swagger.params['deviceId'].value;
  var methodInvokeParameters = req.swagger.params['methodInvokeParameters'].value;
  Module.module_InvokeDeviceMethod(connectionId,deviceId,methodInvokeParameters)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_InvokeModuleMethod = function module_InvokeModuleMethod (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var deviceId = req.swagger.params['deviceId'].value;
  var moduleId = req.swagger.params['moduleId'].value;
  var methodInvokeParameters = req.swagger.params['methodInvokeParameters'].value;
  Module.module_InvokeModuleMethod(connectionId,deviceId,moduleId,methodInvokeParameters)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_PatchTwin = function module_PatchTwin (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var props = req.swagger.params['props'].value;
  Module.module_PatchTwin(connectionId,props)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_Reconnect = function module_Reconnect (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var forceRenewPassword = req.swagger.params['forceRenewPassword'].value;
  Module.module_Reconnect(connectionId,forceRenewPassword)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_RoundtripMethodCall = function module_RoundtripMethodCall (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var methodName = req.swagger.params['methodName'].value;
  var requestAndResponse = req.swagger.params['requestAndResponse'].value;
  Module.module_RoundtripMethodCall(connectionId,methodName,requestAndResponse)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_SendEvent = function module_SendEvent (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var eventBody = req.swagger.params['eventBody'].value;
  Module.module_SendEvent(connectionId,eventBody)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_SendOutputEvent = function module_SendOutputEvent (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var outputName = req.swagger.params['outputName'].value;
  var eventBody = req.swagger.params['eventBody'].value;
  Module.module_SendOutputEvent(connectionId,outputName,eventBody)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_WaitForConnectionStatusChange = function module_WaitForConnectionStatusChange (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_WaitForConnectionStatusChange(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_WaitForDesiredPropertiesPatch = function module_WaitForDesiredPropertiesPatch (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Module.module_WaitForDesiredPropertiesPatch(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.module_WaitForInputMessage = function module_WaitForInputMessage (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var inputName = req.swagger.params['inputName'].value;
  Module.module_WaitForInputMessage(connectionId,inputName)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
