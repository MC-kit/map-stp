"""csv2sqlite implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

from contextlib import closing

from eliot import start_action

from mapstp.init_metainfo_db import init_metainfo_db
from mapstp.utils import can_override

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


def summary2sqlite(summary: Path, sql: Path, *, override: bool = False) -> None:
    """Convert data from ``csv`` to sqlite data base.

    Parameters
    ----------
    summary
        path to CSV file
    sql
        path to output sql
    """
    can_override(sql, override=override)
    with (
        start_action(action_type="convert GeoUNED summary to sqlite", summary=summary) as logger,
        closing(sq.connect(sql)) as con,
        closing(con.cursor()) as cur,
    ):
        init_metainfo_db(cur, "summary2sqlite")
        cur.executemany(
            """
                insert into cells
                    (cell, volume, path)
                values
                    (?, ?, ?)
            """,
            load_records(summary),
        )
        con.commit()
        logger.add_success_fields(sql=sql)


def load_records(
    summary: Path,
) -> Generator[tuple[int, float, str]]:
    """Load records from summary table file created by GeoUNED.

    Parameters
    ----------
    summary
        path to GeoUNED summary file

    Yields
    ------
    The records
    """
    with summary.open(encoding="utf8") as fid:
        try:
            next(fid)  # skip header
        except StopIteration:
            msg = "Input table file is empty"
            raise ValueError(msg) from None
        for line in fid:
            cell = int(line[0:9])
            volume = float(line[34:48])
            path = line[51:]
            yield cell, volume, path
