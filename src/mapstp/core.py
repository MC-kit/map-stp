from typing import List

import sys

from pathlib import Path

import pandas as pd

from mapstp.merge import merge_paths
from mapstp.utils.io import can_override


def create_stp_comments(override, output, paths, mcnp, path_info, separator) -> None:
    if output:
        p = Path(output)
        can_override(p, override)
        _output = p.open(mode="w", encoding="cp1251")
    else:
        _output = sys.stdout
    try:
        merge_paths(_output, paths, path_info, mcnp, separator)
    finally:
        if _output is not sys.stdout:
            _output.close()


def create_excel(
    excel: Path,
    paths: List[List[str]],
    path_info,
    separator,
    start_cell_number,
) -> None:
    df = path_info.copy()
    df["STP path"] = list(map(lambda x: separator.join(x), paths))
    df["cell"] = list(range(start_cell_number, len(paths) + start_cell_number))
    df.set_index(keys="cell", inplace=True)
    with pd.ExcelWriter(excel) as xlsx:
        df.to_excel(xlsx, sheet_name="Cells")
