@REM Copyright (c) Microsoft. All rights reserved.
@REM Licensed under the MIT license. See LICENSE file in the project root for full license information.

@setlocal
@echo off

set sdk-root=%1
rem // resolve to fully qualified path
for %%i in ("%sdk-root%") do set sdk-root=%%~fi

if not exist %sdk-root%\azureiot.sln (
  echo ERROR: file %sdk-root%\azureiot.sln does not exist
  echo.
  echo usage: %0 [csharp-sdk-root]
  exit /b 1
)

if exist sdk\ (
  if not exist sdk\azureiot.sln (
    echo sdk link exists, but azureiot.sln is missing.
    goto failure
  ) else (
    echo SDK link already exists in "%~dp0\sdk"
  )
) else (
  mklink /d sdk %sdk-root%
  if errorlevel 1 (
      echo Error making link to %sdk-root%
      goto :failure
  )
)

echo Open "%~dp0\wrapper\src\edge-e2e.sln" in Visual Studio to debug
echo success
exit /b 0

:failure
echo failure
exit /b 1