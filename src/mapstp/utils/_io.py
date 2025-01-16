"""Input/output utility methods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TextIO

import os
import sys

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from mapstp.utils._re import (
    CELL_START_PATTERN,
    MCNP_SECTIONS_SEPARATOR_PATTERN,
    VOID_CELL_START_PATTERN,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

PathLike = str | Path | os.PathLike[Any]


def can_override(path: Path, *, override: bool) -> Path:
    """Check if it's allowed to override a `path`.

    Args:
        path: path, where we are going to write
        override: permission to override flag

    Returns:
        The input `path` to facilitate chaining in mapping in code.

    Raises:
        FileExistsError: if file exists, but override is not allowed.
    """
    if not override and path.exists():
        msg = (
            f"File {path} already exists."
            "Consider to use '--override' command line option or remove the file."
        )
        raise FileExistsError(msg)
    return path


def find_first_cell_number(mcnp: str | Path) -> int:
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
                return int(match["number"])
    msg = f"Cells are not found in {mcnp}. Is it MCNP file?"
    raise ValueError(msg)


def find_first_void_cell_number(mcnp: str | Path) -> int:
    """Find the first void cell number in MCNP model.

    Args:
        mcnp: an input MCNP model file name

    Returns:
        the first void cell number

    Raises:
        ValueError: if the cell is not found in the `mcnp` file.
    """
    _mcnp = Path(mcnp)
    with _mcnp.open(encoding="cp1251") as stream:
        for line in stream:
            match = VOID_CELL_START_PATTERN.search(line)
            if match:
                return int(match["number"])
    msg = f"Void cells are not found in {mcnp}. Is it MCNP file?"
    raise ValueError(msg)


@contextmanager
def select_output(
    output: PathLike | None = None,
    *,
    override: bool,
) -> Iterator[TextIO]:
    """Select stream for output.

    If the `output` is specified, then checks if we can override it.

    Args:
        output: optional file name for output stream
        override: permission to override, if `output` file exists

    Yields:
        stdout, if `output` file name is  not specified (None),
                opened stream
    """
    if output:
        p = Path(output)
        can_override(p, override=override)
        _output: TextIO = p.open(mode="w", encoding="utf8")
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
    surfaces: str | None = None
    cards: str | None = None
    remainder: str | None = None


def read_mcnp_sections(mcnp_path: Path) -> MCNPSections:
    """Read text sections from MCNP file.

    Args:
        mcnp_path: path to file.

    Returns:
        MCNPSections: - the text sections
    """
    sections = MCNP_SECTIONS_SEPARATOR_PATTERN.split(
        mcnp_path.read_text(encoding="cp1251"),
        maxsplit=3,
    )
    sections_len = len(sections)
    cells = sections[0].strip()
    surfaces = sections[1].strip() if sections_len >= 2 else None
    cards = sections[2].strip() if sections_len >= 3 else None
    if sections_len >= 4:
        remainder: str | None = sections[3].strip()
        if not remainder:
            remainder = None
    else:
        remainder = None
    return MCNPSections(cells, surfaces, cards, remainder)
