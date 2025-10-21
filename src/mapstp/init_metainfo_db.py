"""Shared code to initialize metainfo db."""

from __future__ import annotations

from typing import TYPE_CHECKING

from packaging.version import parse as parse_version

from mapstp import __version__

version_info = parse_version(__version__).release

if TYPE_CHECKING:
    import sqlite3 as sq


def init_metainfo_db(cur: sq.Cursor, command: str) -> None:
    """Initialize metainfo database.

    Parameters
    ----------
    cur
        The database cursor
    command
        which created the database
    """
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
                patch int,
                command text
            )
            """,
    )
    major, minor, patch = version_info
    cur.execute(
        """
            insert into versions
            (application, major, minor, patch, command)
            values
            (?, ?, ?, ?, ?)
            """,
        ("mapstp", major, minor, patch, command),
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
