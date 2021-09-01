#!/usr/bash

deps=(
  Pygments
  black
  codecov
  coverage
  darglint
  flake8
  flake8-annotations
  flake8-bandit
  flake8-bugbear
  flake8-docstrings
  flake8-import-order
  mypy
  pre-commit
  pytest
  pytest-benchmark
  pytest-cov
  pytest-mock
  safety
  sphinx-autodoc-typehints
  sphinx-autorun
  sphinx-rtd-theme
  sphinxcontrib-napoleon
  xdoctest
  rstcheck
  isort
  yappi
)

poetry add --dev ${deps[@]}
