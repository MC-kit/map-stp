"""The module implements algorithms to transform MCNP model.

Inserts end comments with information about path in STP
corresponding to a cell and sets materials and densities,
if specified in STP paths.

"""
from typing import Generator, Iterable, List, Optional, TextIO, Tuple, Union

import math

from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path

import pandas as pd

from mapstp.exceptions import PathInfoError
from mapstp.materials import drop_material_cards
from mapstp.utils.io import read_mcnp_sections
from mapstp.utils.re import CELL_START_PATTERN

logger = getLogger()


def is_defined(number: Union[int, float, None]) -> bool:
    """Check if number coming from a DataFrame object cell is not None or NaN.

    Args:
        number: value to

    Returns:
        true - if `number` is a valid number,
        false - otherwise
    """
    return number is not None and number is not pd.NA and not math.isnan(number)


def extract_number_and_density(
    row: int, path_info: pd.DataFrame
) -> Optional[Tuple[int, float]]:
    """Extract material number and density from a `path_info` for a given `row`.

    Validate the values: number, if provided, is to be positive, density - not
    negative.

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
        msg = f"The `density` value is not defined for material number {number}."
        raise PathInfoError(msg, row, path_info)

    if number <= 0:
        msg = "The values in `number` column are to be positive."
        raise PathInfoError(msg, row, path_info)

    if density < 0:
        msg = "The values in `density` column cannot be negative."
        raise PathInfoError(msg, row, path_info)

    if is_defined(factor):
        if factor < 0.0:
            msg = "The values in `factor` column cannot be negative."
            raise PathInfoError(msg, row, path_info)
        density *= factor

    return number, density


def _correct_first_line(
    _line: str, match_end: int, current_path_idx: int, path_info: pd.DataFrame
) -> str:

    nd = extract_number_and_density(current_path_idx, path_info)

    if nd is not None:
        number, density = nd
        _line = (
            _line[: match_end - 1]
            + f" {int(number)} {-density:.5g}"
            + _line[match_end:]
        )

    return _line


@dataclass
class _Merger:
    paths: List[str]
    path_info: pd.DataFrame
    mcnp_lines: Iterable[str]
    first_cell: bool = field(init=False, default=True)
    current_path_idx: int = field(init=False, default=0)
    paths_length: int = field(init=False)

    def __post_init__(self) -> None:
        self.first_cell = True
        self.cells_over = False
        self.current_path_idx = 0
        self.paths_length = len(self.paths)

    def format_comment(self) -> str:
        comment = f"      $ stp: {self.paths[self.current_path_idx]}"
        self.current_path_idx += 1
        return comment

    def merge_lines(self) -> Generator[str, None, None]:
        for line in self.mcnp_lines:
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
                    if self.current_path_idx < self.paths_length:
                        yield self.format_comment()
                yield line
            else:
                yield line
        if self.current_path_idx < self.paths_length:
            yield self.format_comment()
        if self.current_path_idx != self.paths_length:
            logger.warning(
                f"Only {self.current_path_idx} cells merged, "
                f"STP specifies {self.paths_length} bodies."
            )


def _merge_lines(
    paths: List[str],
    path_info: pd.DataFrame,
    mcnp_lines: Iterable[str],
) -> Generator[str, None, None]:
    merger = _Merger(paths, path_info, mcnp_lines)
    yield from merger.merge_lines()


def merge_paths(
    output: TextIO,
    paths: List[str],
    path_info: pd.DataFrame,
    mcnp: Path,
    used_materials_text: Optional[str] = None,
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
        used_materials_text: The specification of materials to add to model.
    """
    mcnp_sections = read_mcnp_sections(mcnp)
    cells = mcnp_sections.cells
    lines = cells.split("\n")

    for line in _merge_lines(paths, path_info, lines):
        print(line, file=output)

    print(file=output)

    surfaces = mcnp_sections.surfaces
    if surfaces:
        print(surfaces, file=output, end="")
        print("\n\n", file=output, end="")

        cards = mcnp_sections.cards
        if cards:
            cards = cards.strip()
            if used_materials_text:
                used_materials_text = used_materials_text.strip()
                print(used_materials_text, file=output)
                cards_lines = cards.split("\n")
                for line in drop_material_cards(cards_lines):
                    print(line, file=output)
            else:
                print(cards, file=output, end="")
            print("\n\n", file=output)

            remainder = mcnp_sections.remainder
            if remainder:
                print(remainder, file=output, end="")
        else:
            print(used_materials_text, file=output)
    else:
        logger.warning(
            "There are no surfaces in model, "
            "skipping surfaces and data cards including materials"
        )


def join_paths(paths: List[List[str]], separator: str = "/") -> List[str]:
    """Collect rows of strings to string.

    Args:
        paths: list of stp paths defined as list of strings
        separator: character to be used as separator

    Returns:
        list of joined stp paths
    """
    return [separator.join(path) for path in paths]
