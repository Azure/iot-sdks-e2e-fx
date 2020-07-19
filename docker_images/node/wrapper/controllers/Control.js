'use strict';

var utils = require('../utils/writer.js');
var Control = require('../service/ControlService');

module.exports.control_Cleanup = function control_Cleanup (req, res, next) {
  Control.control_Cleanup()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.control_GetCapabilities = function control_GetCapabilities (req, res, next) {
  Control.control_GetCapabilities()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.control_GetWrapperStats = function control_GetWrapperStats (req, res, next) {
  Control.control_GetWrapperStats()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.control_LogMessage = function control_LogMessage (req, res, next) {
  var logMessage = req.swagger.params['logMessage'].value;
  Control.control_LogMessage(logMessage)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.control_SendCommand = function control_SendCommand (req, res, next) {
  var cmd = req.swagger.params['cmd'].value;
  Control.control_SendCommand(cmd)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.control_SetFlags = function control_SetFlags (req, res, next) {
  var flags = req.swagger.params['flags'].value;
  Control.control_SetFlags(flags)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
