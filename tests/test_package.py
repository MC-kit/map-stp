"""Test if installed package is of the current version."""

from __future__ import annotations

import re

from pathlib import Path
from re import sub as substitute

from mapstp import __version__


def _find_version_from_project_toml() -> str:
    toml_path = Path(__file__).parent.parent / "pyproject.toml"
    assert toml_path.exists()
    with toml_path.open() as stream:
        for line in stream:
            _line = line.strip()
            if _line.startswith("version"):
                return _line.split("=")[1].strip().strip('"')
        msg = f"Cannot find item 'version' in {toml_path}"
        raise ValueError(msg)


_VERSION_NORM_PATTERN = re.compile(r"-(?P<letter>.)[^.]*\.(?P<prepatch>.*)$")


def _normalize_version(version: str) -> str:
    return substitute(_VERSION_NORM_PATTERN, r"\1\2", version)


def test_package() -> None:
    """This test checks if only current version is installed in working environment."""
    version = _find_version_from_project_toml()
    assert __version__ == _normalize_version(version), "Run 'uv sync'"
