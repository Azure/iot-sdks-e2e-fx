'use strict';

var utils = require('../utils/writer.js');
var Net = require('../service/NetService');

module.exports.net_Disconnect = function net_Disconnect (req, res, next) {
  var disconnectType = req.swagger.params['disconnectType'].value;
  Net.net_Disconnect(disconnectType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.net_DisconnectAfterC2d = function net_DisconnectAfterC2d (req, res, next) {
  var disconnectType = req.swagger.params['disconnectType'].value;
  Net.net_DisconnectAfterC2d(disconnectType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.net_DisconnectAfterD2c = function net_DisconnectAfterD2c (req, res, next) {
  var disconnectType = req.swagger.params['disconnectType'].value;
  Net.net_DisconnectAfterD2c(disconnectType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.net_Reconnect = function net_Reconnect (req, res, next) {
  Net.net_Reconnect()
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};

module.exports.net_SetDestination = function net_SetDestination (req, res, next) {
  var ip = req.swagger.params['ip'].value;
  var transportType = req.swagger.params['transportType'].value;
  Net.net_SetDestination(ip,transportType)
    .then(function (response) {
      utils.writeJson(res, response);
    })
    .catch(function (response) {
      utils.writeJson(res, response);
    });
};
