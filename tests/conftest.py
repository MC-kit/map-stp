from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

import pytest

from mapstp.materials_index import load_materials_index

if TYPE_CHECKING:
    import pandas as pd


_DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def data() -> Path:
    """Compute the path to test data.

    Returns
    -------
    Path: to test data (absolute).
    """
    return _DATA.absolute()


@pytest.fixture(scope="session")
def materials() -> pd.DataFrame:
    """Materials dataframe."""
    return load_materials_index()


@pytest.fixture
def cd_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporarily change to temp directory.

    Returns
    -------
    Path: to temporary directory
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path
