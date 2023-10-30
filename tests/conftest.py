from __future__ import annotations

from typing import TYPE_CHECKING

import os

from pathlib import Path

import pytest

from mapstp.materials_index import load_materials_index
from mapstp.stp_parser import parse_path
from mapstp.tree import create_bodies_paths
from mapstp.utils.resource import path_resolver

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pandas as pd


@pytest.fixture(scope="session")
def data() -> Path:
    return path_resolver("tests")("data")


@pytest.fixture(scope="session")
def materials() -> pd.DataFrame:
    return load_materials_index()


@pytest.fixture(scope="session")
def paths_ei(data) -> list[list[str]]:
    _stp = Path(data / "test-extract-info.stp")
    products, links = parse_path(_stp)
    return create_bodies_paths(products, links)


@pytest.fixture()
def cd_tmpdir(tmp_path: Path) -> Iterator[Path]:
    """Temporarily switch to temp directory.

    Args:
        tmp_path: pytest fixture for temp directory path

    Yields:
        temporary path
    """
    old_dir = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_dir)
