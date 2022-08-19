"""Input/output utility methods."""
from typing import Generator, Optional, TextIO, Union

import os
import sys

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from loguru import logger
from mapstp.utils.re import CELL_START_PATTERN, MCNP_SECTIONS_SEPARATOR_PATTERN

PathLike = Union[str, Path, os.PathLike]


def can_override(path: Path, override: bool) -> Path:
    """Check if it's allowed to override a `path`.

    Args:
        path: path, where we are going to write
        override: permission to override flag

    Returns:
        The input `path`to facilitate chaining in mapping in code.

    Raises:
        FileExistsError: if file exists, but override is not allowed.
    """
    if not override and path.exists():
        raise FileExistsError(
            f"File {path} already exists."
            "Consider to use '--override' command line option or remove the file."
        )
    return path


def find_first_cell_number(mcnp: Union[str, Path]) -> int:
    """Find the first cell number in MCNP model.

    Args:
        mcnp: an input MCNP model file name

    Returns:
        the first cell number

    Raises:
        ValueError: if the cell is not found in the `mcnp` file.
    """
    _mcnp = Path(mcnp)
    with _mcnp.open(encoding="cp1251") as stream:
        for line in stream:
            match = CELL_START_PATTERN.search(line)
            if match:
                cell_number = int(line[: match.end()].split()[0])
                return cell_number
    raise ValueError(f"Cells with material 0 are not found in {mcnp}. Is it MCNP file?")


@contextmanager
def select_output(
    override: bool,
    output: Optional[PathLike] = None,
) -> Generator[TextIO, None, None]:
    """Select stream for output.

    If the `output` is specified, then checks if we can override it.

    Args:
        override: permission to override, if `output` file exists
        output: optional file name for output stream

    Yields:
        stdout, if `output` file name is  not specified (None),
                opened stream

    """
    if output:
        p = Path(output)
        can_override(p, override)
        _output: TextIO = p.open(mode="w", encoding="cp1251")
        logger.info("Tagged mcnp will be saved to {}", p)
    else:
        _output = sys.stdout
    try:
        yield _output
    finally:
        if _output is not sys.stdout:
            _output.close()


@dataclass
class MCNPSections:
    """Text sections from an MCNP file."""

    cells: str
    surfaces: Optional[str] = None
    cards: Optional[str] = None
    remainder: Optional[str] = None


def read_mcnp_sections(mcnp_path: Path) -> MCNPSections:
    """Read text sections from MCNP file.

    Args:
        mcnp_path: path to file.

    Returns:
        MCNPSections: - the text sections

    """
    sections = MCNP_SECTIONS_SEPARATOR_PATTERN.split(
        mcnp_path.read_text(encoding="cp1251"), maxsplit=3
    )
    sections_len = len(sections)
    cells = sections[0].strip()
    surfaces = sections[1].strip() if 2 <= sections_len else None
    cards = sections[2].strip() if 3 <= sections_len else None
    if 4 <= sections_len:
        remainder: Optional[str] = sections[3].strip()
        if remainder == "":
            remainder = None
    else:
        remainder = None
    return MCNPSections(cells, surfaces, cards, remainder)
