@rem Copyright (c) Microsoft. All rights reserved.
@rem Licensed under the MIT license. See LICENSE file in the project root for full license information.
@echo off

set script_dir=%~dp0

if "%_HORTON_%" == "" (
    call %script_dir%\activate_horton.cmd
    if errorlevel 1 ( echo "failed to activate horton" && goto :failure)
)

python %script_dir%/horton.py %*
if errorlevel 1 ( echo "horton.py failed" && goto :failure)

exit /b 0

:failure
exit /b 1
