"""csv2sqlite implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

from contextlib import closing

import pandas as pd

from eliot import start_action

from mapstp import __version__
from mapstp.utils import can_override

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

version_info = tuple(int(x) for x in __version__.split("."))


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
        cur.execute(
            """
            drop table if exists versions;
            """,
        )
        cur.execute(
            """
            create table versions (  -- the applications may store their DB schema version here
                application text primary key,
                major int,
                minor int,
                patch int
            )
            """,
        )
        major, minor, patch = version_info
        cur.execute(
            """
            insert into versions
            (application, major, minor, patch)
            values
            (?, ?, ?, ?)
            """,
            ("mapstp", major, minor, patch),
        )
        cur.execute(
            """
            drop table if exists cells;
            """,
        )
        cur.execute(
            """
            create table cells (
                cell integer primary key,
                volume real,      -- volume computed by SpaceClaim
                xmin real,        -- bounding box boundaries
                ymin real,
                zmin real,
                xmax real,
                ymax real,
                zmax real,
                path text unique,   -- path to body in SpaceClaim
                material integer,  -- mapstp will update this and the following
                density real,
                correction real,   -- density correction factor
                rwcl text         -- rwcl tag
            );
            """,
        )
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
