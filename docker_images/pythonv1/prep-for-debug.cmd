@REM Copyright (c) Microsoft. All rights reserved.
@REM Licensed under the MIT license. See LICENSE file in the project root for full license information.

@echo off
@setlocal enabledelayedexpansion

set sdk-root=%1
rem // resolve to fully qualified path
for %%i in ("%sdk-root%") do set sdk-root=%%~fi

if not exist %sdk-root%\device\iothub_client_python (
  echo ERROR: directory %sdk-root%\device\iothub_client_python does not exist
  echo.
  echo usage: %0 [python-sdk-root]
  exit /b 1
)

if "%VSCMD_VER%" == "" (
  echo ERROR: this script must be called from a VS build window
  exit /b 1
)
pushd %sdk-root%\build_all\windows
if errorlevel 1 (
  echo failure: couldn't pushd to %sdk-root%\build_all\windows
  exit /b %ERRORLEVEL%
)

set _step=build.cmd
set build-config=Debug
call build_client.cmd --config %build-config%
if errorlevel 1 set _ERROR_=%ERRORLEVEL% && goto :failure
popd

set cmake-output=cmake_x64
set _step=copying binaries
cd %~dp0wrapper\swagger_server
copy %USERPROFILE%\%cmake-output%\python\src\%build-config%\iothub_client.pyd .
if errorlevel 1 set _ERROR_=%ERRORLEVEL% && goto :failure
copy %USERPROFILE%\%cmake-output%\python_service_client\src\%build-config%\iothub_service_client.pyd .
if errorlevel 1 set _ERROR_=%ERRORLEVEL% && goto :failure
copy %USERPROFILE%\%cmake-output%\python\src\%build-config%\iothub_client.pdb .
if errorlevel 1 set _ERROR_=%ERRORLEVEL% && goto :failure
copy %USERPROFILE%\%cmake-output%\python_service_client\src\%build-config%\iothub_service_client.pdb .
if errorlevel 1 set _ERROR_=%ERRORLEVEL% && goto :failure

popd
echo success
exit /b 0

:failure
popd
echo failure in %_step%
exit /b %_ERROR_%
