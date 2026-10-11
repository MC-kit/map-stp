from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

import pytest

from mapstp.__main__ import app as mapstp
from mapstp.cli.summary2sqlite import load_records

from ._check_cells_table import check_cells_table

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.fixture
def summary(data: Path) -> Path:
    """Get path to test csv file."""
    return (data / "geouned-summary-1.txt").absolute()


@pytest.fixture
def scsv(summary: Path) -> str:
    """Get path to test csv file as string."""
    return str(summary)


def test_load_records(summary: Path) -> None:
    records = list(load_records(summary))
    assert len(records) == 3
    cell, volume, path = records[0]
    assert cell == 1
    assert volume == 7.0052e4
    assert path.startswith("/trt-5.0.1/")


def test_help_command(cyclopts_runner: Callable[..., str]) -> None:
    out = cyclopts_runner(mapstp, ["summary2sqlite", "--help"])
    assert "Convert GeoUNED summary" in out


def test_happy_path(cyclopts_runner: Callable[..., str], scsv: str) -> None:
    sql = Path("test-happy-path.sqlite")
    cyclopts_runner(mapstp, ["summary2sqlite", "--sql", str(sql), scsv])
    check_cells_table(sql)
