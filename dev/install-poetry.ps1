#
# poetry can be installed with this script
#

# Notes:
#    - Installing poetry with conda works but with some flaws: poetry cannot update itself and complains that its' "not installed with recommended installer"
#
#    - Recent poetry installation instructions for Windows: https://python-poetry.org/docs/master/#installation

# Poetry
#
# set environment variable POETRY_HOME in advance, if you need nonstandard or shared poetry installation.
#
# windows powershell install instructions
# stable (to be deprecated):
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py -UseBasicParsing).Content | python -
# recent
# download and run script https://install.python-poetry.org

