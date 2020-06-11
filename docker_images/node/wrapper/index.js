'use strict';
// added in merge
/*jshint esversion: 6 */

var fs = require('fs'),
    path = require('path'),
    http = require('http'),
    spawn = require('child_process').spawn;

var app = require('connect')();
var swaggerTools = require('swagger-tools');
var jsyaml = require('js-yaml');
var serverPort = 8080;

// swaggerRouter configuration
var options = {
  swaggerUi: path.join(__dirname, '/swagger.json'),
  controllers: path.join(__dirname, './controllers'),
  useStubs: process.env.NODE_ENV === 'development' // Conditionally turn on stubs (mock mode)
};

// The Swagger document (require it, build it programmatically, fetch it from a URL, ...)
var spec = fs.readFileSync(path.join(__dirname,'api/swagger.yaml'), 'utf8');
var swaggerDoc = jsyaml.safeLoad(spec);

// BEGIN code added in merge
// Function to convert PascalCase to camelCase
var toCamel = function(s) {
    return s.charAt(0).toLowerCase() + s.slice(1)
}

// operationId values in the yaml are PascalCased, but the code generator
// gave us functions that are camelCased.  Fix this up.
var paths = swaggerDoc.paths
Object.keys(paths).forEach(function(path) {
  ['get', 'put', 'post', 'patch'].forEach(function(verb) {
    if (paths[path][verb] && paths[path][verb].operationId) {
      paths[path][verb].operationId = toCamel(paths[path][verb].operationId);
    }
  });
}); 

// spawn net watcher
/*
const net_control_app = spawn('python', ['/net_control_app/main.py']);
net_control_app.stdout.on('data', (data) => {  console.log(`net_control_app: ${data}`);});
net_control_app.stderr.on('data', (data) => {  console.log(`net_control_app: ${data}`);});
*/
// END code added in merge

// Initialize the Swagger middleware
swaggerTools.initializeMiddleware(swaggerDoc, function (middleware) {

  // Interpret Swagger resources and attach metadata to request - must be first in swagger-tools middleware chain
  app.use(middleware.swaggerMetadata());

  // Validate Swagger requests
  app.use(middleware.swaggerValidator());

  // Route validated requests to appropriate controller
  app.use(middleware.swaggerRouter(options));

  // Serve the Swagger documents and Swagger UI
  app.use(middleware.swaggerUi());

  // Start the server
  http.createServer(app).listen(serverPort, function () {
    console.log('Your server is listening on port %d (http://localhost:%d)', serverPort, serverPort);
    console.log('Swagger-ui is available on http://localhost:%d/docs', serverPort);
  });

});
