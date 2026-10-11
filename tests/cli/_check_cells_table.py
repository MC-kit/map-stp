from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

from contextlib import closing

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path


def check_cells_table(sql: Path) -> None:
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
