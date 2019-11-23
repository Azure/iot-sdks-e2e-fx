// Copyright (c) Microsoft. All rights reserved.^M
// Licensed under the MIT license. See LICENSE file in the project root for full license information.
'use strict';
const fs = require('fs')

let lerna = JSON.parse(fs.readFileSync('./lerna.json'));

var new_packages = ['wrapper']
lerna.packages.forEach(function(name) {
    if (name != 'edge-e2e/wrapper/nodejs-server-server') {
        new_packages.push('sdk/' + name)
    }
});
lerna.packages = new_packages;

fs.writeFileSync('./lerna.json', JSON.stringify(lerna, null, 2))



