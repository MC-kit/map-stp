@echo off
::
:: Prepare conda environment for mapstp development on Windows.
::
:: dvp, Nov 2021
::

if "%1"=="--help" (
    echo.
    echo Usage:
    echo.
    echo "reset-conda-env <conda_env> <python_version>"
    echo.
    echo All the parameters are optional.
    echo.
    echo Defaults:
    echo 	conda_env=mapstp-2
::    echo   install_tool=pip   another valid value: poetry
    echo   python_version=3.9
    echo.
    goto END
)

set conda_env=%1
shift
if "%conda_env%"=="" set conda_env=mapstp-2

set python_vesion=%1
shift
if "%python_vesion%"=="" set python_vesion=3.8

call poetry --version > NUL
if errorlevel 1 (
	echo ERROR\: Poetry is not available
	echo Run dev\install-poetry.bat
	echo or see poetry installation instructions: https://python-poetry.org
	goto END

)

echo Installing conda environment %conda_env%

call conda deactivate
call conda activate
call conda env remove -n %conda_env% -q -y
call conda create -n %conda_env%
:: python=%python_version% -q -y
call conda activate %conda_env%
python --version
conda update -q -y pip wheel setuptools


::   this makes poetry to use conda environment and don't create own one
call poetry config --local virtualenvs.create false
::   this creates egg-link in the environment to current project (development install)

goto END

call poetry install

if errorlevel 1  (
    echo "ERROR: failed to run install with %install_tool%"
    goto END
)

mapstp --version
if errorlevel 1  (
    echo "ERROR: failed to install mapstp"
    goto END
)
echo.
echo SUCCESS: mapstp has been installed into conda environment %conda_env%
echo.


pytest -m "not slow"
if errorlevel 1 (
    echo ERROR: failed to run tests
    goto END
)
echo.
echo SUCCESS: pytest is passed OK
echo.



if "%install_tool%"=="poetry" (
    :: verify nox
    nox --list
    :: safety first - run this on every dependency addition or update
    :: test often - who doesn't?
    nox -s safety -s tests -p %python_version% -- -m "not slow" --cov
    call poetry build
    if errorlevel 1 (
        echo ERROR: failed to run poetry build
        goto END
    )
) else (
    pip install .
    if errorlevel 1 (
        echo ERROR: failed to collect dependencies with pip
        goto END
    )
)

call create-jk %mapstp%
if errorlevel 1 (
    goto END
)

echo.
echo SUCCESS!
echo --------
echo.
echo Usage:
echo.
mapstp --help
echo.
echo Conda environment %mapstp% is all clear.
echo Set your IDE to use %CONDA_PREFIX%\python.exe
echo.
echo Enjoy!
echo.


:END
