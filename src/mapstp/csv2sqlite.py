"""csv2sqlite implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

from contextlib import closing

import pandas as pd

from eliot import start_action

from mapstp.init_metainfo_db import init_metainfo_db
from mapstp.utils import can_override

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


def csv2sqlite(csv: Path, sql: Path, *, override: bool = False) -> None:
    """Convert data from ``csv`` to sqlite data base.

    Parameters
    ----------
    csv
        path to CSV file
    sql
        path to output sql
    """
    can_override(sql, override=override)
    with (
        start_action(action_type="convert csv to sqlite", csv=csv) as logger,
        closing(sq.connect(sql)) as con,
        closing(con.cursor()) as cur,
    ):
        init_metainfo_db(cur, "csv2sqlite")
        cur.executemany(
            """
                insert into cells
                    (cell, volume, xmin, ymin, zmin, xmax, ymax, zmax, path)
                values
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            load_records(csv),
        )
        con.commit()
        logger.add_success_fields(sql=sql)


def load_records(
    csv: Path,
) -> Generator[tuple[int, float, float, float, float, float, float, float, str]]:
    """Load records from CSV file created in SpaceClaim with extract-info script.

    Parameters
    ----------
    csv
        path to csv file

    Yields
    ------
    The records
    """
    df = pd.read_csv(csv)
    yield from df.itertuples(index=False)
