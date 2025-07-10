"""Major methods to create accompanying Excel output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlite3 as sq

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path


def combine_cell_table(
    joined_paths: list[str],
    path_info: pd.DataFrame,
    start_cell_number: int = 1,
    volumes_map: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Combine table with information associated with cells.

    Args:
        joined_paths: STP paths for each cell
        path_info: number, density, factor for each cell
        start_cell_number: number to start cell numbering in the Excel, default 1
        volumes_map: json with cell volumes, optional

    Returns:
         The dataframe with cell, material, density, factor, rwcl id, STP path and volume.
    """
    temp_df = path_info.copy()
    temp_df["STP path"] = joined_paths
    paths_length = len(joined_paths)
    temp_df["cell"] = list(range(start_cell_number, paths_length + start_cell_number))
    columns = [
        "cell",
        "material_number",
        "density",
        "factor",
        "rwcl",
        "volume",
        "STP path",
    ]
    if volumes_map:
        temp_df["volume"] = np.empty((paths_length,), dtype=float)
        temp_df = temp_df.set_index("STP path")
        for k, v in volumes_map.items():
            temp_df.loc[k[1:], "volume"] = v  # omit the first '/'
        temp_df = temp_df.reset_index()
    else:
        temp_df["volume"] = None
    temp_df = temp_df[columns]
    return temp_df.set_index("cell")


def create_excel(
    excel: Path,
    cell_info: pd.DataFrame,
) -> None:
    """Write Excel file presenting information for each cell.

     The information includes material number, density, fraction applied, rwcl id, and STP path.

    Args:
        excel: output Excel file name
        cell_info: table with information associated with cells
    """
    with pd.ExcelWriter(excel) as xlsx:
        cell_info.to_excel(xlsx, sheet_name="Cells")


# noinspection SqlNoDataSourceInspection,SqlResolve
def create_sql(
    sql: Path,
    cell_info: pd.DataFrame,
) -> None:
    """Write Excel file presenting information for each cell.

    The information includes material number, density, fraction applied, rwcl id, and STP path.

    Note:
        stp_path is not unique: cells corresponding to linked bodies have the same stp path

    Args:
        sql: output SQLite3 file name
        cell_info: table with information associated with cells
    """
    with sq.connect(sql) as con:
        # noinspection SqlNoDataSourceInspection
        cur = con.cursor()
        cur.executescript(
            """
            drop table if exists cell_info;
            create table cell_info (
                cell integer primary key,
                material_number integer,
                density real,
                factor real,
                rwcl text,
                volume real,
                stp_path text
            );
            """,
        )
        cur.executemany(
            """
            insert into cell_info(cell, material_number, density, factor, rwcl, volume, stp_path)
            values(?,?,?,?,?,?,?)
            """,
            list(map(tuple, cell_info.reset_index().itertuples(index=False))),
        )
