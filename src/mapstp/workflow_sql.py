"""The module contains workflow methods for SQL storage.

The storage is produced with extract-volumes script from SpaceClaim.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from logging import getLogger

import pandas as pd

from mapstp.extract_info import define_material_number_and_density, extract_meta_info_from_path
from mapstp.materials_index import load_materials_index

if TYPE_CHECKING:
    import sqlite3 as sq


def _add_materials(con: sq.Connection, material_index: pd.DataFrame) -> None:
    records = con.execute(
        """
        select cell, path from cells
        """,
    ).fetchall()

    def _iter_records():
        for cell, path in records:
            meta_info = extract_meta_info_from_path(path)
            if meta_info.mnemonic:
                density, material = define_material_number_and_density(
                    material_index,
                    meta_info,
                    path,
                )
                yield material, density, meta_info.factor, cell

    con.executemany(
        """
        update cells
        set
            material = ?,
            density = ?,
            factor = ?
        where cell = ?
        """,
        _iter_records(),
    )
    con.commit()


def create_cells_table(
    con: sq.Connection,
    materials_index: str,
    start_cell_number: int = 1,
) -> None:
    """Store information from materials index corresponding to cells paths to SQL database.

    The database should contain a table number_path_volume, which has been generated
    with extract-volumes.py script from SpaceClaim. The numbers in this table are zero
    based index of cells in MCNP model.

    Args:
        con: connection to database
        materials_index: file name of materials index file.
        start_cell_number: the first cell number
    """
    logger = getLogger()
    _materials_index = load_materials_index(materials_index)
    logger.info("Loaded material index from {}", materials_index)
    con.execute("drop table if exists cells")
    con.execute(
        """
        create table cells (
            cell int primary key,
            material int,
            density  int,
            factor real,
            volume real,
            path text
        )
        """,
    )
    con.execute(
        """
        insert into cells
            (
                cell,
                volume,
                path
            )
        select
            (number + ?) cell,
            volume,
            path
        from
            number_path_volume
        order by cell
        """,
        (start_cell_number,),
    )
    con.commit()
    _add_materials(con, _materials_index)


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
            material material_number,
            density,
            factor,
            volume,
            path
        from
            cells
        order by
            cell
        """,
        con,
    )
