'use strict';

var utils = require('../utils/writer.js');
var Service = require('../service/ServiceService');

module.exports.service_Connect = function service_Connect (req, res, next) {
  var connectionString = req.swagger.params['connectionString'].value;
  Service.service_Connect(connectionString)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.service_Disconnect = function service_Disconnect (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  Service.service_Disconnect(connectionId)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.service_InvokeDeviceMethod = function service_InvokeDeviceMethod (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var deviceId = req.swagger.params['deviceId'].value;
  var methodInvokeParameters = req.swagger.params['methodInvokeParameters'].value;
  Service.service_InvokeDeviceMethod(connectionId,deviceId,methodInvokeParameters)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.service_InvokeModuleMethod = function service_InvokeModuleMethod (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var deviceId = req.swagger.params['deviceId'].value;
  var moduleId = req.swagger.params['moduleId'].value;
  var methodInvokeParameters = req.swagger.params['methodInvokeParameters'].value;
  Service.service_InvokeModuleMethod(connectionId,deviceId,moduleId,methodInvokeParameters)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.service_SendC2d = function service_SendC2d (req, res, next) {
  var connectionId = req.swagger.params['connectionId'].value;
  var eventBody = req.swagger.params['eventBody'].value;
  Service.service_SendC2d(connectionId,eventBody)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
