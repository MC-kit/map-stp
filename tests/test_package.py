from __future__ import annotations

import re

from pathlib import Path
from re import sub as substitute

from mapstp import __version__


def find_version_from_project_toml():
    toml_path = Path(__file__).parent.parent / "pyproject.toml"
    assert toml_path.exists()
    with toml_path.open() as stream:
        for line in stream:
            _line = line.strip()
            if _line.startswith("version"):
                return _line.split("=")[1].strip().strip('"')
        raise ValueError(f"Cannot find item 'version' in {toml_path}")


_VERSION_NORM_PATTERN = re.compile(r"-(?P<letter>.)[^.]*\.(?P<prepatch>.*)$")


def normalize_version(version: str):
    return substitute(_VERSION_NORM_PATTERN, r"\1\2", version)


def test_package():
    version = find_version_from_project_toml()
    assert __version__ == normalize_version(version), "Run 'poetry install'"
