@REM Copyright (c) Microsoft. All rights reserved.
@REM Licensed under the MIT license. See LICENSE file in the project root for full license information.
@echo off

if not exist sdk\nul (
    if not exist %1\lerna.json (
        echo usage: %0 [node_root]
        echo e.g.: %0 f:\repos\node
        exit /b 1
    )

    mklink /j sdk %1 
    if errorlevel 1 ( echo error calling mklink && exit /b 1 )
)

copy sdk\package.json .
if errorlevel 1 ( echo cp package.json failed && exit /b 1 )

call npm install
if errorlevel 1 ( echo npm install failed && exit /b 1 )

copy sdk\lerna.json .
if errorlevel 1 ( echo cp lerna.json failed && exit /b 1 )

node fixLerna.js
if errorlevel 1 ( echo fixLerna.js failed && exit /b 1 )

call lerna bootstrap  --scope iot-sdk-device-client-rest-api --include-dependencies
if errorlevel 1 ( echo lerna bootstrap failed && exit /b 1 )

call lerna run build --scope iot-sdk-device-client-rest-api --include-dependencies
if errorlevel 1 ( echo lerna run build failed && exit /b 1 )

echo success!

