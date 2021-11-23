@echo off 
echo Installing Poetry using python script.
echo .
if "%POETRY_HOME%" == "" (
	@echo standard poetry location is %USERPROFIL%\.poetry
	@echo set environment variable POETRY_HOME in advance, if you need non-standard or shared poetry installation.
) else (
	@echo Poetry location is %POETRY_HOME%
)
echo .
echo The script has been downloaded from https://install.python-poetry.org at 2021-11-22, update it if necessary.
echo .
python %~dp0\install-poetry.py


