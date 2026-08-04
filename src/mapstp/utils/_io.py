"""Input/output utility methods."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mapstp.utils._re import (CELL_START_PATTERN,
                              MCNP_SECTIONS_SEPARATOR_PATTERN,
                              VOID_CELL_START_PATTERN)

PathLike = str | Path | os.PathLike[Any]


def can_override(path: Path, *, override: bool = False) -> Path:
    """Check if it's allowed to override a `path`.

    Parameters
    ----------
    path
        path, where we are going to write
    override
        permission to override flag

    Returns
    -------
    The input `path` to facilitate chaining in mapping in code.

    Raises
    ------
    FileExistsError: if file exists, but override is not allowed.
    """
    if not override and path.exists():
        msg = f"File {path} already exists.Consider to use '--override' command line option or remove the file."
        raise FileExistsError(msg)
    return path


def find_first_cell_number(mcnp: str | Path) -> int:
    """Find the first cell number in MCNP model.

    Parameters
    ----------
    mcnp
        an input MCNP model file name

    Returns
    -------
    the first cell number

    Raises
    ------
    ValueError: if the cell is not found in the ``mcnp`` file.
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

    Parameters
    ----------
    mcnp
        an input MCNP model file name

    Returns
    -------
    the first void cell number

    Raises
    ------
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


@dataclass
class MCNPSections:
    """Text sections from an MCNP file."""

    cells: str
    surfaces: str | None = None
    cards: str | None = None
    remainder: str | None = None


def read_mcnp_sections(mcnp_path: Path, encoding: str = "utf8") -> MCNPSections:
    """Read text sections from MCNP file.

    Parameters
    ----------
    mcnp_path
        path to file.
    encoding
        input file encoding, for MCNP generated with GEOUNED it's ``utf8``, for SuperMC - ``cp1251``

    Returns
    -------
    MCNPSections: - the text sections
    """
    sections = MCNP_SECTIONS_SEPARATOR_PATTERN.split(
        mcnp_path.read_text(encoding=encoding),
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
