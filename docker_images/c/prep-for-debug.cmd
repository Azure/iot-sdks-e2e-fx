@REM Copyright (c) Microsoft. All rights reserved.
@REM Licensed under the MIT license. See LICENSE file in the project root for full license information.

@setlocal
@echo off

set sdk-root=%1
rem // resolve to fully qualified path
for %%i in ("%sdk-root%") do set sdk-root=%%~fi

pushd

if not exist %sdk-root%\CMakeLists.txt (
  echo ERROR: file %sdk-root%\CMakeLists.txt does not exist
  echo.
  echo usage: %0 [c-sdk-root]
  goto :failure
)

if "%VSCMD_VER%" == "" (
  echo ERROR: this script must be called from a VS build window
  goto :failure
)

@rem -------------------------------------------------------------
@rem Make a clone of the restbed repo
rd /q /s %~dp0\wrapper\deps\restbed
mkdir %~dp0\wrapper\deps\restbed
if errorlevel 1 echo "mkdir restbed failed" && goto :failure

cd %~dp0\wrapper\deps\restbed
if errorlevel 1 echo "cd restbed failed" && goto :failure

git clone https://github.com/Corvusoft/restbed .
if errorlevel 1 echo "git clone failed" && goto :failure

git checkout 1b43b9a
if errorlevel 1 echo "git checkout failed" && goto :failure

git submodule update --init --recursive
if errorlevel 1 echo "git checkout failed" && goto :failure

@rem -------------------------------------------------------------
@rem pull the tests out of the CMakeLists file
findstr -v {PROJECT_SOURCE_DIR}/test/ CMakeLists.txt > temp.txt
if errorlevel 1 echo "findstr -v failed" && goto :failure

copy temp.txt CMakeLists.txt
if errorlevel 1 echo "copy temp.txt CMakeLists.txt failed" && goto :failure

mkdir %~dp0\wrapper\build
cd %~dp0\wrapper\build
if errorlevel 1 echo "cd build failed" && goto :failure

cmake -D use_edge_modules=ON  -D skip_samples=ON -D C_SDK_ROOT=%sdk-root% ..
if errorlevel 1 echo "cmake failed" && goto :failure

msbuild project.sln /t:edge_e2e_rest_server /p:Configuration=Debug
if errorlevel 1 echo "msbuild failed" && goto :failure

popd
echo success
exit /b 0

:failure
popd
echo failure
exit /b 1