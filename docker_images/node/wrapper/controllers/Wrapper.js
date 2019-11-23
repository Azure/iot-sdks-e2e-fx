'use strict';

var utils = require('../utils/writer.js');
var Wrapper = require('../service/WrapperService');

module.exports.wrapper_Cleanup = function wrapper_Cleanup (req, res, next) {
  Wrapper.wrapper_Cleanup()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.wrapper_GetCapabilities = function wrapper_GetCapabilities (req, res, next) {
  Wrapper.wrapper_GetCapabilities()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.wrapper_LogMessage = function wrapper_LogMessage (req, res, next) {
  var msg = req.swagger.params['msg'].value;
  Wrapper.wrapper_LogMessage(msg)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.wrapper_SendCommand = function wrapper_SendCommand (req, res, next) {
  var cmd = req.swagger.params['cmd'].value;
  Wrapper.wrapper_SendCommand(cmd)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.wrapper_SetFlags = function wrapper_SetFlags (req, res, next) {
  var flags = req.swagger.params['flags'].value;
  Wrapper.wrapper_SetFlags(flags)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
