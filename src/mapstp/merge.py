"""The module implements algorithms to transform MCNP model.

Inserts end comments with information about path in STP
corresponding to a cell and sets materials and densities,
if specified in STP paths.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, TextIO

import math

from dataclasses import dataclass, field
from logging import getLogger

import pandas as pd

from mapstp.exceptions import PathInfoError
from mapstp.materials import drop_material_cards
from mapstp.utils.io import read_mcnp_sections
from mapstp.utils.re import CELL_START_PATTERN

if TYPE_CHECKING:
    import re

    from collections.abc import Iterable, Iterator
    from pathlib import Path

    from mapstp.utils.io import MCNPSections

logger = getLogger()


def is_defined(number: float | None) -> bool:
    """Check if number coming from a DataFrame object cell is not None or NaN.

    Args:
        number: value to

    Returns:
        true - if `number` is a valid number,
        false - otherwise
    """
    return number is not None and number is not pd.NA and not math.isnan(number)


def extract_number_and_density(row: int, path_info: pd.DataFrame) -> tuple[int, float] | None:
    """Extract material number and density from a `path_info` for a given `row`.

    Validate the values: number, if provided, is to be positive, density - not
    negative.

    Args:
        row: point the row in `path_info`
        path_info: table of data extracted from materials index for a given STP path.

    Returns:
        number and density or None, if not available
    """
    material_number, density, factor = path_info.iloc[row][["material_number", "density", "factor"]]

    def _validate(expr: bool, msg: str):
        if not expr:
            raise PathInfoError(msg, row, path_info)

    if not is_defined(material_number):
        return None  # void space

    _validate(
        is_defined(density),
        f"The `density` value is not defined for material number {material_number}.",
    )
    _validate(material_number > 0, "The values in `number` column are to be positive.")
    _validate(density >= 0.0, "The values in `density` column cannot be negative.")

    if is_defined(factor):
        _validate(
            factor >= 0.0,
            "The values in `factor` column cannot be negative.",
        )
        density *= factor

    return material_number, density


def _correct_first_line(
    _line: str,
    match_end: int,
    current_path_idx: int,
    path_info: pd.DataFrame,
) -> str:
    nd = extract_number_and_density(current_path_idx, path_info)

    if nd is not None:
        material_number, density = nd
        return (
            _line[: match_end - 1] + f" {int(material_number)} {-density:.5g}" + _line[match_end:]
        )

    return _line


@dataclass
class _Merger:
    paths: list[str]
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
        i = self.current_path_idx
        self.current_path_idx += 1
        return f"      $ stp: {self.paths[i]}"

    def merge_lines(self) -> Iterator[str]:
        for line in self.mcnp_lines:
            match = CELL_START_PATTERN.match(line)
            if match:
                yield from self._on_cell_start(line, match)
            else:
                yield line
        if self.current_path_idx < self.paths_length:
            yield self.format_comment()
        if self.current_path_idx != self.paths_length:
            logger.warning(
                "Only {} cells merged, STP specifies {} bodies.",
                self.current_path_idx,
                self.paths_length,
            )

    def _on_cell_start(self, line: str, match: re.Match) -> Iterator[str]:
        if self.first_cell:
            line = self._on_first_cell(line, match)
        else:
            line = self._on_next_cell(line, match)
            if self.current_path_idx < self.paths_length:
                yield self.format_comment()
        yield line

    def _on_next_cell(self, line: str, match: re.Match) -> str:
        first_cell_line_info_row = self.current_path_idx + 1
        if first_cell_line_info_row < self.paths_length:
            line = _correct_first_line(
                line,
                match.end(),
                first_cell_line_info_row,
                self.path_info,
            )
        return line

    def _on_first_cell(self, line: str, match: re.Match) -> str:
        line = _correct_first_line(line, match.end(), self.current_path_idx, self.path_info)
        self.first_cell = False
        return line


def _merge_lines(
    paths: list[str],
    path_info: pd.DataFrame,
    mcnp_lines: Iterable[str],
) -> Iterator[str]:
    merger = _Merger(paths, path_info, mcnp_lines)
    yield from merger.merge_lines()


def merge_paths(
    output: TextIO,
    paths: list[str],
    path_info: pd.DataFrame,
    mcnp: Path,
    used_materials_text: str | None = None,
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

    _print_other_sections(mcnp_sections, output, used_materials_text)


def _print_other_sections(
    mcnp_sections: MCNPSections,
    output: TextIO,
    used_materials_text: str,
) -> None:
    surfaces = mcnp_sections.surfaces
    if surfaces:
        print(surfaces, file=output, end="")
        print("\n\n", file=output, end="")

        cards = mcnp_sections.cards
        remainder = mcnp_sections.remainder
        if cards:
            _print_control_cards_with_used_materials(
                cards,
                remainder,
                output,
                used_materials_text,
            )
        else:
            print(used_materials_text, file=output)
    else:
        logger.warning(
            "There are no surfaces in model, "
            "skipping surfaces and data cards including materials",
        )


def _print_control_cards_with_used_materials(
    cards: str,
    remainder: str | None,
    output: TextIO,
    used_materials_text: str,
) -> None:
    if used_materials_text:
        used_materials_text = used_materials_text.strip()
        print(used_materials_text, file=output)
        cards_lines = cards.strip().split("\n")
        for line in drop_material_cards(cards_lines):
            print(line, file=output)
    else:
        print(cards, file=output, end="")
    print("\n\n", file=output)
    if remainder:
        print(remainder, file=output, end="")


def join_paths(paths: list[list[str]], separator: str = "/") -> list[str]:
    """Collect rows of strings to string.

    Note:
        if stp path contains more than one part,
        then omit the first part, which in that case is duplicated in
        all the stp paths, to be consistent with names in volumes.json.

    Args:
        paths: list of stp paths defined as list of strings
        separator: character to be used as separator

    Returns:
        list of joined stp paths
    """

    def select_unique_parts(path: list[str]) -> list[str]:
        if len(path) > 1:
            return path[1:]
        return path

    return [separator.join(select_unique_parts(path)) for path in paths]
