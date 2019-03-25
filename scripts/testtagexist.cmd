@ECHO OFF
setlocal

if [%~1]==[] goto :no_arg

powershell -command "& './Tag-DockerImage.ps1' 'bertk-csharp-lkg' %1 '--VerifyTagExists'; exit $LASTEXITCODE"

IF NOT ERRORLEVEL 1 GOTO success
    echo FAIL: Tag does NOT exist in repository
    goto end_test:

:success
    echo SUCCESS: Tag exists in repository.
    goto end_test:

:no_arg
    echo ERROR: Please supply TagName as arg1
    goto end_test:

:end_test
    echo Test Completed.
endlocal
