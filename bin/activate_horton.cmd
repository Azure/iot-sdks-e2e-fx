@rem Copyright (c) Microsoft. All rights reserved.
@rem Licensed under the MIT license. See LICENSE file in the project root for full license information.
@echo off

set script_dir=%~dp0
set root_dir=%~dp0\..
pushd %root_dir%

if not exist %script_dir%\_virtualenv\horton\Scripts\activate.bat (
    echo Initializing horton environment 

    rmdir /q /s %script_dir%\_python
    mkdir %script_dir%\_python

    echo Installing Python 3.8.1
    nuget install python -Version 3.8.1 -OutputDirectory %script_dir%\_python
    if errorlevel 1 ( echo "nuget install pythin invalled" && goto :failure)

    echo Installing virtualEnv library
    %script_dir%\_python\python.3.8.1\tools\python -m pip -q install virtualenv
    if errorlevel 1 ( echo "failed to install virtualenv" && goto :failure)

    echo Creating virtual environment
    %script_dir%_python\python.3.8.1\tools\python -m virtualenv %script_dir%\_virtualenv\horton --prompt "(horton) "
    if errorlevel 1 ( echo "failed to create virtual environment" && goto :failure)
    
    echo Activating virtual environment
    call %script_dir%_virtualenv\horton\Scripts\activate.bat
    if errorlevel 1 ( echo "failed to activate virtualenv" && goto :failure)
    
    echo Installing horton libraries
    pip install -q --upgrade pip && ^
pip install -q -r %root_dir%\requirements.txt && ^
pip install -q -e %root_dir%\horton_helpers\ && ^
pip install -q -e %root_dir%\docker_images\pythonv2\wrapper\python_glue\
    if errorlevel 1 ( echo "failed to install horton libraries" && goto :failure)
) else (
    call %script_dir%_virtualenv\horton\Scripts\activate.bat
    if errorlevel 1 ( echo "failed to activate virtualenv" && goto :failure)
)

set _HORTON_=1
echo Horton environment activated
exit /b 0

:failure
exit /b 1

