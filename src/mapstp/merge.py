"""
The module implements algorithms to transform MCNP model.

Inserts end comments with information about path in STP
corresponding to a cell and sets materials and densities,
if specified in STP paths.

"""

from typing import Generator, Iterable, List, Optional, TextIO, Tuple

from pathlib import Path

import pandas as pd

from mapstp.utils.re import CELL_START_PATTERN, CELLS_END_PATTERN


def extract_number_and_density(
    row: int, path_info: pd.DataFrame
) -> Optional[Tuple[int, float]]:
    """Extract material number and density from a `path_info` for a given `row`.

    Args:
        row: point the row in `path_info`
        path_info: table of data extracted from materials index for a given STP path.

    Returns:
        number and density or None, if not available

    Raises:
        ValueError: when the resulting values are out of valid ranges

    """
    number, density, factor = path_info.iloc[row][["number", "density", "factor"]]

    if number is None or density is None:
        return None

    if number <= 0:
        raise ValueError("The values in `number` column are to be positive")

    if density < 0:
        raise ValueError("The values in `density` column cannot be negative")

    if factor is not None:
        if factor < 0.0:
            raise ValueError("The values in `factor` column cannot be negative")
        density *= factor

    return number, density


def _correct_first_line(
    _line: str, match_end: int, current_path_idx: int, path_info: pd.DataFrame
) -> str:

    nd = extract_number_and_density(current_path_idx, path_info)

    if nd is not None:
        number, density = nd
        _line = _line[: match_end - 1] + f" {number} {-density:.5g}" + _line[match_end:]

    return _line


def merge_lines(
    paths: List[List[str]],
    path_info: pd.DataFrame,
    mcnp_lines: Iterable[str],
    separator: str = "/",
) -> Generator[str, None, None]:
    first_cell = True
    cells_over = False
    current_path_idx = 0

    def format_comment() -> str:
        nonlocal current_path_idx
        comment = f"      $ stp: {separator.join(paths[current_path_idx])}\n"
        current_path_idx += 1
        return comment

    for line in mcnp_lines:

        if cells_over or len(paths) <= current_path_idx:
            yield line
        else:
            if CELLS_END_PATTERN.match(line):
                if first_cell:
                    raise ValueError("Incorrect MCNP file: no cells.")
                if current_path_idx < len(paths):
                    yield format_comment()
                yield line
                assert (
                    len(paths) <= current_path_idx
                ), f"Only {current_path_idx} merged, expected  {len(paths)}"
                cells_over = True
            else:
                match = CELL_START_PATTERN.match(line)
                if match:
                    if first_cell:
                        line = _correct_first_line(
                            line, match.end(), current_path_idx, path_info
                        )
                        first_cell = False
                    else:
                        first_cell_line_info_row = current_path_idx + 1
                        if first_cell_line_info_row < len(paths):
                            line = _correct_first_line(
                                line, match.end(), first_cell_line_info_row, path_info
                            )
                        yield format_comment()
                    yield line
                else:
                    yield line


def merge_paths(
    output: TextIO,
    paths: List[List[str]],
    path_info: pd.DataFrame,
    mcnp: Path,
    separator: str = "/",
) -> None:
    with mcnp.open(encoding="cp1251") as mcnp_stream:
        for line in merge_lines(paths, path_info, mcnp_stream.readlines(), separator):
            print(line, file=output, end="")
