@REM Copyright (c) Microsoft. All rights reserved.
@REM Licensed under the MIT license. See LICENSE file in the project root for full license information.

@setlocal
@echo off

if not exist %~dp0\wrapper\build\Project.sln (
  echo ERROR: file %~dp0wrapper\build\Project.sln does not exist.  You need to run prep-for-debug.cmd first.
  echo.
  exit /b 1
)

if "%VSCMD_VER%" == "" (
  echo ERROR: this script must be called from a VS build window
  exit /b 1
)

start %~dp0\wrapper\build\Project.sln
echo success
exit /b 0

