from __future__ import annotations

from typing import TYPE_CHECKING

import shutil
import sqlite3 as sq

from contextlib import closing
from pathlib import Path

import pandas as pd
import pytest

from mapstp.__main__ import app as mapstp

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def csv(data: Path) -> Path:
    """Get path to test csv file."""
    return (data / "test1-component-volumes.csv").absolute()


@pytest.fixture
def scsv(csv: Path) -> str:
    """Get path to test csv file as string."""
    return str(csv)


def test_help_command(cyclopts_runner: Callable) -> None:
    out = cyclopts_runner(mapstp, ["csv2sqlite", "--help"])
    assert "Convert CSV" in out


def test_happy_path(cyclopts_runner: Callable, scsv: str) -> None:
    sql = Path("test-happy-path.sqlite")
    cyclopts_runner(mapstp, ["csv2sqlite", "--sql", str(sql), scsv])
    assert sql.exists(), f"Should create {sql}"
    with closing(sq.connect(sql)) as con:
        df = pd.read_sql("select * from cells", con)
        expected_columns = {
            "cell",
            "volume",
            "xmin",
            "ymin",
            "zmin",
            "xmax",
            "ymax",
            "zmax",
            "path",
            "material",
            "density",
            "correction",
            "rwcl",
        }
        actual_columns = set(df.columns)
        assert actual_columns == expected_columns
        df = pd.read_sql("select * from cells", con)
        assert df.shape == (3, 13)


@pytest.mark.skip(reason="Run only to create some new test CSV file")
def test_prepare_test_csv(data: Path, cd_tmpdir: Path) -> None:  # noqa: ARG001
    original_sql = data / "test1.sqlite"
    with closing(sq.connect(original_sql)) as con:
        df = pd.read_sql("select * from cells", con)
        df = df[df.columns[:-4]]
        out = Path("test1-component-volumes.csv")
        df.to_csv(out, index=False)
        assert out.exists()
        shutil.copy(out, data)
