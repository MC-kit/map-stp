@echo off
::
:: Prepare conda environment for mapstp development on Windows.
::
:: dvp, Nov 2021
::

:: defaults
set conda_env=mapstp
set python_version=3.10


call :main %*

if ""%ERRORLEVEL%"" NEQ "0" (echo SUCCESS.) else (echo FAIL!)

goto END

:main
    if "%1"=="--help" (
        call :usage
    ) else (
        call :arg_parse %*
        call :reset_conda
    )
    goto END

:usage
    echo.
    echo Usage:
    echo.
    echo "reset-conda-env <conda_env> <python_version>"
    echo.
    echo All the parameters are optional.
    echo.
    echo Defaults:
    echo    conda_env=%conda_env%
    echo    python_version=%python_version%
    echo.

:arg_parse
    if "%1" NEQ "" (
        set set conda_env=%1
        shift
        if "%1" NEQ "" set python_version=%1
    )
    goto END

:reset_conda
    echo Installing environment %conda_env% for Python %python_version%
    call conda deactivate
    call conda activate
    call conda env remove -n %conda_env% -q -y
    call conda create -n %conda_env% python=%python_version% pip -c conda-forge -q -y
    if "%ERRORLEVEL%" NEQ "0" (
        echo Probably conda has problems with antivirus,  try delete AppData/Temp pip files.
    ) else (
        call conda activate %conda_env%
        python --version
    )
    goto END

:END
