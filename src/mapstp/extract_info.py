"""Extract meta information from paths given in an STP file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import re

from dataclasses import dataclass

import numpy as np
import pandas as pd

_META_PATTERN = re.compile(r"\[(?P<meta>[^]]+)]")

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class MetaInfoCollector:
    """Helper to store meta information from a path."""

    mnemonic: str | None = None
    factor: float | None = None
    rwcl: str | None = None

    def update(self: MetaInfoCollector, pars: dict[str, str]) -> None:
        """Revise meta information collected on traversing along an STP branch.

        Args:
            pars: the last found meta information
        """
        mnemonic = pars.get("m")
        if mnemonic is not None:
            if mnemonic == "void":
                # all subsequent components in the STP tree are void,
                # except linked ones, if any
                self.mnemonic = None
                self.factor = None
            else:
                self.mnemonic = mnemonic

        t = pars.get("f")
        if t is not None:
            self.factor = float(t)

        t = pars.get("r")
        if t is not None:
            self.rwcl = t


def extract_path_info(paths: list[str], material_index: pd.DataFrame) -> pd.DataFrame:
    """Extract meta information from `paths` and associate corresponding data with each path.

    Args:
        paths: STP paths
        material_index: mnemonic-material-density lookup table

    Returns:
        Table with material `number`, `density`, applied correction `factor`,
        and `rwcl` label corresponding to every path in paths
    """
    return pd.DataFrame.from_records(
        _records(paths, material_index),
        columns=["material_number", "density", "factor", "rwcl"],
    )


def _records(
    paths: list[str],
    material_index: pd.DataFrame,
) -> Iterator[tuple[int | None, float | None, float | None, str | None]]:
    for path in paths:
        meta_info = extract_meta_info_from_path(path)
        if meta_info.mnemonic:
            density, material_number = define_material_number_and_density(
                material_index,
                meta_info,
                path,
            )
        else:
            material_number = density = None
        yield material_number, density, meta_info.factor, meta_info.rwcl


def define_material_number_and_density(
    material_index: pd.DataFrame,
    meta_info: MetaInfoCollector,
    path: str,
) -> tuple[float | None, int | None]:
    """Define material number and density from a material index for given meta info.

    Args:
        material_index: table mapping material mnemonics to material number and density
        meta_info: ... collected from the `path`
        path: ... for diagnostics

    Returns:
        density and material
    """
    try:
        material_number: int | None = int(material_index.loc[meta_info.mnemonic]["number"])
    except KeyError:
        msg = (
            f"The mnemonic {meta_info.mnemonic!r} "
            "is not specified in the material index. "
            f"See the STP path: {path}"
        )
        raise KeyError(msg) from None
    density = material_index.loc[meta_info.mnemonic]["density"]
    if np.isnan(density):
        msg = (
            f"The density for mnemonic {meta_info.mnemonic!r} "
            "is not specified in the material index."
        )
        raise ValueError(msg)
    if density < 0.0:
        msg = (
            f"The density for mnemonic {meta_info.mnemonic!r} "
            "in the material index is not to be negative."
        )
        raise ValueError(msg)
    return density, material_number


def extract_meta_info_from_path(path: str) -> MetaInfoCollector:
    """Extract meta information from an STP path.

    Args:
        path: ... to body with `[m-...]` tags

    Returns:
        Collected meta info map.
    """
    meta_info = MetaInfoCollector()
    found = _META_PATTERN.findall(path)
    if found:
        for meta in found:
            pairs = _extract_meta_info(meta, path)
            meta_info.update(pairs)
    return meta_info


def _extract_meta_info(meta: str, path: str) -> dict[str, str]:
    try:
        pairs: dict[str, str] = dict(_create_pair(t) for t in meta.split())
    except ValueError as _ex:
        msg = f"On path {path}"
        raise ValueError(msg) from _ex
    return pairs


def _create_pair(meta_part: str) -> tuple[str, str]:
    a, b = meta_part.split("-", maxsplit=1)
    return a, b
