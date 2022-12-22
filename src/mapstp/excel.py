"""Major methods to create accompanying Excel output file."""

from typing import List

from pathlib import Path

import pandas as pd


def create_excel(
    excel: Path,
    paths: List[List[str]],
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
    df = path_info.copy()
    df["STP path"] = [separator.join(x) for x in paths]
    df["cell"] = list(range(start_cell_number, len(paths) + start_cell_number))
    df.set_index(keys="cell", inplace=True)
    with pd.ExcelWriter(excel) as xlsx:
        df.to_excel(xlsx, sheet_name="Cells")
