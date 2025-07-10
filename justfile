set dotenv-load := true

default_python := "3.13"
TITLE := `uv version`
VERSION := `uv version --short`

default:
  @just --list

# create uv venv
venv:
  [ -d .venv ] || uv venv --python {{default_python}}

# build package
build: venv
  uv build

# clean reproducible files
clean:
  #!/bin/bash
  to_clean=(
      ".benchmarks"
      ".cache"
      ".eggs"
      ".mypy_cache"
      ".nox"
      ".pytest_cache"
      ".ruff_cache"
      "__pycache__"
      "_skbuild"
      "build"
      "dist"
      "docs/_build"
      "htmlcov"
      "setup.py"
  )
  rm -fr ${to_clean[@]}


# install package
install: build
  uv sync   

# clean build
reinstall: clean install

# test up to the first fail
test-ff *ARGS:
  pytest -vv -x {{ARGS}}

# test with clean cache
test-cache-clear *ARGS:
  pytest -vv --cache-clear {{ARGS}}

# test fast
test-fast *ARGS:
  pytest -m "not slow" {{ARGS}}

# run all the tests
test-all *ARGS:
  pytest {{ARGS}}

# check correct typing at runtime
typeguard *ARGS:
  uv run --no-dev --group test --group typeguard pytest -vv --emoji --typeguard-packages=src {{ARGS}}

# run documentation tests 
xdoctest *ARGS:
  uv run --no-dev --group test --group xdoctest python -m xdoctest --silent --style google -c all src tools {{ARGS}}

# create coverage data
coverage:
  @uv run --no-dev --group coverage coverage run --parallel -m pytest
  @uv run --no-dev --group coverage coverage combine
  @uv run --no-dev --group coverage coverage report

# coverage to html
coverage-html: coverage
  @uv run --no-dev --group coverage coverage html

# Run pre-commit on all files
pre-commit:
  @uv run --no-dev --group pre-commit pre-commit run -a 

# Run mypy
mypy:
  @uv run --no-dev --group mypy mypy src docs/source/conf.py


# Check style and test all
check-all: pre-commit test-all

bump *ARGS:
  #!/bin/bash
  uv version --bump {{ARGS}}
  git commit -m "bump: version $(uv version)" pyproject.toml uv.lock 


# Update dependencies
up:
  @pre-commit autoupdate
  @uv self update

# Check rst-texts
rstcheck:
  @rstcheck *.rst docs/source/*.rst

docs-build: rstcheck
  @uv run --no-dev --group docs sphinx-build docs/source docs/_build

docs:
  @uv run --no-dev --group docs --group docs-auto sphinx-autobuild --open-browser docs/source docs/_build

ruff:
  @ruff check --fix src tests
  @ruff format src tests


# Aliases
alias t := test-all
alias c := check-all
