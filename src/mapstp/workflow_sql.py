"""The module contains workflow methods for SQL storage.

The storage is produced with extract-volumes script from SpaceClaim.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from logging import getLogger

import pandas as pd

from mapstp.extract_info import (
    define_material_number_and_density,
    extract_meta_info_from_path,
)
from mapstp.materials_index import load_materials_index

if TYPE_CHECKING:
    import sqlite3 as sq

    from collections.abc import Generator


def save_meta_info_from_paths(con: sq.Connection, materials_index: str) -> None:
    """Store information from materials index corresponding to cells paths to SQL database.

    The database should contain a table cells, which has been generated
    with extract-info.py script from SpaceClaim. The numbers in this table are
    index of cells in MCNP model (starting from 1).

    Args:
        con: connection to database
        materials_index: file name of materials index file.
    """
    logger = getLogger()
    _materials_index = load_materials_index(materials_index)
    logger.info("Loaded material index from {}", materials_index)

    records = con.execute(
        """
        select cell, path from cells order by cell
        """,
    ).fetchall()

    def _iter_records() -> Generator[
        tuple[int | None, float | None, float | None, str | None, int | None]
    ]:
        for cell, path in records:
            meta_info = extract_meta_info_from_path(path)
            if meta_info.mnemonic:
                density, material = define_material_number_and_density(
                    _materials_index,
                    meta_info,
                    path,
                )
                yield material, density, meta_info.factor, meta_info.rwcl, cell

    con.executemany(
        """
        update cells
        set
            material = ?,
            density = ?,
            correction = ?,
            rwcl = ?
        where cell = ?
        """,
        _iter_records(),
    )
    con.commit()


def load_path_info(con: sq.Connection) -> pd.DataFrame:
    """Load 'cells' table from the database.

    Args:
        con: database connection

    Returns:
        the loaded table ordered by cell number
    """
    return pd.read_sql(
        """
        select
            cell,
            volume,
            xmin,
            ymin,
            zmin,
            xmax,
            ymax,
            zmax,
            material material_number,
            density,
            correction factor,
            rwcl,
            path
        from
            cells
        order by
            cell
        """,
        con,
    ).set_index("cell")
