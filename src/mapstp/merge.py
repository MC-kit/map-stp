"""
The module implements algorithms to transform MCNP model.

Inserts end comments with information about path in STP
corresponding to a cell and sets materials and densities,
if specified in STP paths.

"""

from typing import Generator, Iterable, List, Optional, TextIO, Tuple, Union

import math
import warnings

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from mapstp.exceptions import PathInfoError
from mapstp.utils.re import CELL_START_PATTERN, CELLS_END_PATTERN


def is_defined(number: Union[int, float]) -> bool:
    """Check if number coming from a DataFrame object cell is not None or NaN.

    Args:
        number: value to

    Returns:
        true - if `number` is a valid number,
        false - otherwise
    """
    return number is not None and not math.isnan(number)


def is_not_defined(number: Union[int, float]) -> bool:
    """Check if number coming from a DataFrame object cell is None or NaN.

    Args:
        number: value to check

    Returns:
        true - if `number` is not defined,
        false - otherwise
    """
    return not is_defined(number)


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
        PathInfoError: when the resulting values are out of valid ranges

    """
    number, density, factor = path_info.iloc[row][["number", "density", "factor"]]

    if not is_defined(number):
        return None  # void space

    if not is_defined(density):
        raise PathInfoError(
            f"The `density` value is not defined for material number {number}.",
            row,
            path_info,
        )

    if number <= 0:
        raise PathInfoError(
            "The values in `number` column are to be positive.", row, path_info
        )

    if density < 0:
        raise PathInfoError(
            "The values in `density` column cannot be negative.", row, path_info
        )

    if is_defined(factor):
        if factor < 0.0:
            raise PathInfoError(
                "The values in `factor` column cannot be negative.", row, path_info
            )
        density *= factor

    if math.isnan(density):
        raise PathInfoError("Density is nan.", row, path_info)

    return number, density


def _correct_first_line(
    _line: str, match_end: int, current_path_idx: int, path_info: pd.DataFrame
) -> str:

    nd = extract_number_and_density(current_path_idx, path_info)

    if nd is not None:
        number, density = nd
        _line = _line[: match_end - 1] + f" {number} {-density:.5g}" + _line[match_end:]

    return _line


@dataclass
class _Merger:
    paths: List[List[str]]
    path_info: pd.DataFrame
    mcnp_lines: Iterable[str]
    separator: str = "/"
    first_cell: bool = field(init=False, default=True)
    cells_over: bool = field(init=False, default=False)
    current_path_idx: int = field(init=False, default=0)
    paths_length: int = field(init=False)

    def __post_init__(self) -> None:
        self.first_cell = True
        self.cells_over = False
        self.current_path_idx = 0
        self.paths_length = len(self.paths)

    def format_comment(self) -> str:
        comment = (
            f"      $ stp: {self.separator.join(self.paths[self.current_path_idx])}\n"
        )
        self.current_path_idx += 1
        return comment

    def merge_lines(self) -> Generator[str, None, None]:
        for line in self.mcnp_lines:
            if self.cells_over or self.paths_length <= self.current_path_idx:
                yield line
            else:
                if CELLS_END_PATTERN.match(line):
                    if self.first_cell:
                        raise ValueError("Incorrect MCNP file: no cells.")
                    if self.current_path_idx < self.paths_length:
                        yield self.format_comment()
                    yield line
                    if self.current_path_idx != self.paths_length:
                        warnings.warn(
                            f"Only {self.current_path_idx} merged,"
                            f"expected  {self.paths_length}"
                        )
                    self.cells_over = True
                else:
                    match = CELL_START_PATTERN.match(line)
                    if match:
                        if self.first_cell:
                            line = _correct_first_line(
                                line, match.end(), self.current_path_idx, self.path_info
                            )
                            self.first_cell = False
                        else:
                            first_cell_line_info_row = self.current_path_idx + 1
                            if first_cell_line_info_row < self.paths_length:
                                line = _correct_first_line(
                                    line,
                                    match.end(),
                                    first_cell_line_info_row,
                                    self.path_info,
                                )
                            yield self.format_comment()
                        yield line
                    else:
                        yield line


def _merge_lines(
    paths: List[List[str]],
    path_info: pd.DataFrame,
    mcnp_lines: Iterable[str],
    separator: str = "/",
) -> Generator[str, None, None]:
    merger = _Merger(paths, path_info, mcnp_lines, separator)
    yield from merger.merge_lines()


def merge_paths(
    output: TextIO,
    paths: List[List[str]],
    path_info: pd.DataFrame,
    mcnp: Path,
    separator: str = "/",
) -> None:
    """Print to `output` the updated MCNP code.

    The material numbers and densities are inserted instead of zeroes.
    The STP path is inserted as end of line comment below each corresponding cell.

    Args:
        output: stream to print to
        paths: list of STP paths for each cell
        path_info: table with other information on cells:
                  material number, density, density correction factor.
        mcnp:   The input MCNP file name.
        separator: The character to separate parts in an STP path.
    """
    with mcnp.open(encoding="cp1251") as mcnp_stream:
        for line in _merge_lines(paths, path_info, mcnp_stream.readlines(), separator):
            print(line, file=output, end="")
