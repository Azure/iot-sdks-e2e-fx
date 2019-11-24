'use strict';


/**
 * Simulate a network disconnection
 *
 * disconnectType String disconnect method for dropped connection tests
 * no response value expected for this operation
 **/
exports.net_Disconnect = function(disconnectType) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Simulate a disconnect after the next C2D transfer
 *
 * disconnectType String disconnect method for dropped connection tests
 * no response value expected for this operation
 **/
exports.net_DisconnectAfterC2d = function(disconnectType) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Simulate a disconnect after the next D2C transfer
 *
 * disconnectType String disconnect method for dropped connection tests
 * no response value expected for this operation
 **/
exports.net_DisconnectAfterD2c = function(disconnectType) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Reconnect the network after a simulated network disconnection
 *
 * no response value expected for this operation
 **/
exports.net_Reconnect = function() {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}


/**
 * Set destination for net disconnect ops
 *
 * ip String 
 * transportType String Transport to use
 * no response value expected for this operation
 **/
exports.net_SetDestination = function(ip,transportType) {
  return new Promise(function(resolve, reject) {
    resolve();
  });
}

