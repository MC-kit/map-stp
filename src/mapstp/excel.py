"""Major methods to create accompanying Excel output file."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path


def create_excel(
    excel: Path,
    paths: list[list[str]],
    path_info: pd.DataFrame,
    separator: str,
    start_cell_number: int,
) -> None:
    """Write excel file presenting presenting information for each cell.

     The information includes material number, density, fraction applied, rwcl id, and STP path.

    Args:
        excel: output excel file name
        paths: STP paths for each cell
        path_info: number, density, factor for each cell
        separator: character to separate STP path parts
        start_cell_number: number to start cell numbering in the excel
    """
    temp_df = path_info.copy()
    temp_df["STP path"] = [separator.join(x) for x in paths]
    temp_df["cell"] = list(range(start_cell_number, len(paths) + start_cell_number))
    temp_df = temp_df.set_index(keys="cell")
    with pd.ExcelWriter(excel) as xlsx:
        temp_df.to_excel(xlsx, sheet_name="Cells")
