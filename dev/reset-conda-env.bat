@echo off
::
:: Prepare conda environment for mapstp development on Windows.
::
:: dvp, Nov 2021
::

:: defaults
set conda_env=mapstp
set python_version=3.9


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
        echo Probably conda pip has problems with the Windows AppData cache or temporary files
        echo Try delete AppData/Temp pip files.
    ) else (
        call conda activate %conda_env%
        python --version
        echo Install local copy of poetry: this is conda...
        echo The global poetry won't work in the activated environment.
        call conda install poetry -c conda-forge -q -y
        echo Cache in Windows AppData is out of our control
        mkdir c:\programs\poetry-cache
        call poetry config --local cache-dir c:\programs\poetry-cache
        call poetry config --local virtualenvs.create false
        call poetry install
    )
    goto END

:END
