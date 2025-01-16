"""Code to load materials map.

The map associates material number to its MCNP specification text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TextIO

from collections import defaultdict
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path

import numpy as np

from mapstp.utils._re import CARD_PATTERN, MATERIAL_PATTERN

if TYPE_CHECKING:
    import sqlite3 as sq

    from collections.abc import Callable, Generator, Iterable

    import pandas as pd

MaterialsDict = dict[int, str]
"""Mapping material number -> material MCNP text."""

logger = getLogger()


@dataclass
class _Loader:
    stream: TextIO
    material_no: int = field(default=-1, init=False)
    materials_dict: dict[int, list[str]] = field(
        default_factory=lambda: defaultdict(list),
        init=False,
    )

    def __post_init__(self: _Loader) -> None:
        for line in self.stream:
            self._process_line(line)

    @property
    def _in_material_card(self: _Loader) -> bool:
        return self.material_no > 0

    def _process_line(self: _Loader, line: str) -> None:
        if self._in_material_card:
            match = CARD_PATTERN.search(line)
            if not match:
                self._append(line)
                return
            if match.lastgroup != "comment" and not self._check_if_material_line(line):
                self.material_no = -1
        else:
            self._check_if_material_line(line)

    def _append(self: _Loader, line: str) -> None:
        if self.material_no > 0:
            self.materials_dict[self.material_no].append(line)

    def _check_if_material_line(self: _Loader, line: str) -> bool:
        match = MATERIAL_PATTERN.search(line)
        if match:
            self.material_no = int(match["material"])
            if self.material_no <= 0:
                msg = f"Wrong material number {self.material_no} found"
                raise ValueError(msg)
            if self.material_no in self.materials_dict:
                msg = f"Material number {self.material_no} is duplicated"
                raise ValueError(msg)
            self._append(line)
            return True
        return False  # skipping other cards and prepending text


def load_materials_map_from_stream(stream: TextIO) -> MaterialsDict:
    """Read materials from opened MCNP file.

    Args:
        stream: stream to read from

    Returns:
        MaterialsDict: mapping material number -> material text
    """
    loader = _Loader(stream)

    def _restore_material_text(lines: Iterable[str]) -> str:
        result = "".join(lines)
        if not result.endswith("\n"):
            result += "\n"
        return result

    return {k: _restore_material_text(v) for k, v in loader.materials_dict.items()}


def load_materials_map(materials: str | Path) -> MaterialsDict:
    """Read materials from MCNP file.

    Args:
        materials: name of MCNP file, containing materials to read

    Returns:
        MaterialsDict: mapping material number -> material text
    """
    path = Path(materials)
    with path.open(encoding="cp1251") as stream:
        return load_materials_map_from_stream(stream)


def drop_material_cards(lines: Iterable[str]) -> Generator[str]:
    """Drop lines belonging to material cards.

    Used on replacing materials in the model with ones actually used.

    Args:
        lines: mcnp file split to lines

    Yields:
        all the lines of the model without material cards
    """
    in_material_card = False
    for line in lines:
        match = CARD_PATTERN.search(line)
        if match and match.lastgroup == "card":
            in_material_card = MATERIAL_PATTERN.search(line) is not None
        if not in_material_card:
            yield line


def materials_spec_mapper(materials_map: dict[int, str]) -> Callable[[int], str]:
    """Create method to extract a material specification by its number.

    Args:
        materials_map:  map number -> spec

    Returns:
        method to be used in map extracting material specification.
    """

    def _func(used_number: int) -> str:
        if used_number > 0:
            text = materials_map.get(used_number)
            if not text:
                logger.warning(
                    "Material M%s is not found "
                    "in provided materials specifications. "
                    "A dummy specification is issued to the tagged model.",
                    used_number,
                )
                text = (
                    f"m{used_number}  "
                    "$ dummy: material was not provided to mapstp\n"
                    "        1001.31c  1.0\n"
                )
            return text
        return ""

    return _func


def get_used_materials(materials_map: dict[int, str], path_info: pd.DataFrame) -> str:
    """Collect text of used materials specifications.

    Args:
        materials_map: map material number -> spec.
        path_info: dataframe containing column with used material numbers.

    Returns:
        All the used materials specs to be used as part of MCNP model text.
    """
    values = path_info["material_number"].to_numpy()
    used_numbers = sorted({int(m) for m in values if not np.isnan(m)})
    used_materials_texts = list(map(materials_spec_mapper(materials_map), used_numbers))
    return "".join(used_materials_texts)


def get_used_materials_sql(con: sq.Connection, materials_map: dict[int, str]) -> str:
    """Collect text of used materials specifications.

    Args:
        con: database connection
        materials_map: map material number -> spec.
    """
    used_numbers = [
        x[0]
        for x in con.execute(
            """
            select distinct material
            from cells
            where material not null
            order by material
            """,
        )
    ]
    used_materials_texts = list(map(materials_spec_mapper(materials_map), used_numbers))
    return "".join(used_materials_texts)
