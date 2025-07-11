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
from mapstp.utils import CELL_START_PATTERN, read_mcnp_sections

if TYPE_CHECKING:
    import re

    from collections.abc import Generator, Iterable, Iterator
    from pathlib import Path

    from mapstp.utils import MCNPSections

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


def extract_number_and_density(cell: int, path_info: pd.DataFrame) -> tuple[int, float] | None:
    """Extract material number and density from a `path_info` for a given `cell`.

    Validate the values: number, if provided, is to be positive, density - not
    negative.

    Args:
        cell: index in `path_info`
        path_info: table of data extracted from materials index for a given STP path.

    Returns:
        number and density or None, if not available
    """
    material_number, density, factor = path_info.loc[cell][["material_number", "density", "factor"]]

    def _validate(*, res: bool, msg: str) -> None:
        if not res:
            raise PathInfoError(msg, cell, path_info)

    if not is_defined(material_number):
        return None  # void space

    _validate(
        res=is_defined(density),
        msg=f"The `density` value is not defined for material number {material_number}.",
    )
    _validate(res=material_number > 0, msg="The values in `number` column are to be positive.")
    _validate(res=density >= 0.0, msg="The values in `density` column cannot be negative.")

    if is_defined(factor):
        _validate(
            res=factor >= 0.0,
            msg="The values in `factor` column cannot be negative.",
        )
        density *= factor

    return material_number, density


def _correct_first_line(
    _line: str,
    match_end: int,
    current_cell: int,
    path_info: pd.DataFrame,
) -> str:
    nd = extract_number_and_density(current_cell, path_info)

    if nd is not None:
        material_number, density = nd
        line_with_material_and_density = (
            _line[: match_end - 1].split()[0] + f" {int(material_number)} {-density:.5g}"
        )
        remainder = _line[match_end:].strip()
        if remainder:
            line_with_material_and_density += "\n" + " " * max(match_end, 5) + remainder

        _line = line_with_material_and_density

    return _line


@dataclass
class _Merger:
    path_info: pd.DataFrame
    mcnp_lines: Iterable[str]
    first_cell: bool = field(init=False, default=True)
    cells_over: bool = field(init=False, default=True)
    current_cell: int = field(init=False, default=0)

    def merge_lines(self: _Merger) -> Iterator[str]:
        """Add information to MCNP cells.

        Yields:
            line from a cell descriptions or added information
        """
        for line in self.mcnp_lines:
            match = CELL_START_PATTERN.match(line)
            if match:
                yield from self._on_cell_start(line, match)
            else:
                yield line
        if self.is_current_cell_specified():
            yield from self._format_volume_and_comment()

    def is_current_cell_specified(self: _Merger) -> bool:
        """Check if current cell needs to update the first line and add a comment.

        Returns:
            True, if current cell needs to update the first line and add a comment, False otherwise.
        """
        return self.current_cell in self.path_info.index

    def _format_volume_and_comment(self: _Merger) -> Generator[str]:
        rec = self.path_info.loc[self.current_cell][["volume", "path"]]
        yield f"      vol={rec.volume}"
        yield f"      $ stp: {rec.path}"

    def _on_cell_start(self: _Merger, line: str, match: re.Match[str]) -> Generator[str]:
        if self.first_cell:
            line = self._on_next_cell(line, match)
            self.first_cell = False
        else:
            if self.is_current_cell_specified():
                yield from self._format_volume_and_comment()
            line = self._on_next_cell(line, match)
        yield line

    def _on_next_cell(self: _Merger, line: str, match: re.Match[str]) -> str:
        self.current_cell = int(match["number"])
        if self.is_current_cell_specified() and int(match["material"]) == 0:
            line = _correct_first_line(
                line,
                match.end(),
                self.current_cell,
                self.path_info,
            )
        return line


def _merge_lines(
    path_info: pd.DataFrame,
    mcnp_lines: Iterable[str],
) -> Iterator[str]:
    merger = _Merger(path_info, mcnp_lines)
    yield from merger.merge_lines()


def merge_paths(
    output: TextIO,
    path_info: pd.DataFrame,
    mcnp: Path,
    used_materials_text: str | None = None,
) -> None:
    """Print to `output` the updated MCNP code.

    The material numbers and densities are inserted instead of zeroes.
    The STP path is inserted as end of line comment below each corresponding cell.

    Args:
        output: stream to print to
        path_info: table with other information on cells:
                  material number, density, density correction factor.
        mcnp:   The input MCNP file name.
        used_materials_text: The specification of materials to add to model.
    """
    mcnp_sections = read_mcnp_sections(mcnp)
    cells = mcnp_sections.cells
    lines = cells.split("\n")

    for line in _merge_lines(path_info, lines):
        print(line, file=output)

    print(file=output)

    _print_other_sections(mcnp_sections, output, used_materials_text)


def _print_other_sections(
    mcnp_sections: MCNPSections,
    output: TextIO,
    used_materials_text: str | None,
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
            "There are no surfaces in model, skipping surfaces and data cards including materials",
        )


def _print_control_cards_with_used_materials(
    cards: str,
    remainder: str | None,
    output: TextIO,
    used_materials_text: str | None,
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
