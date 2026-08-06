"""Major methods to create accompanying Excel output file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path


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
