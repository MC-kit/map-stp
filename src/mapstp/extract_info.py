"""Extract meta information from paths given in an STP file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import re

from dataclasses import dataclass

import numpy as np
import pandas as pd

_META_PATTERN = re.compile(r"\[(?P<meta>[mfr]-[^]]+)]")

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

        Parameters
        ----------
        pars
            the last found meta information
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

    Returns
    -------
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
                meta_info.mnemonic,
                path,
            )
        else:
            material_number = density = None
        yield material_number, density, meta_info.factor, meta_info.rwcl


def define_material_number_and_density(
    material_index: pd.DataFrame,
    mnemonic: str,
    path: str,
) -> tuple[float | None, int | None]:
    """Define material number and density from a material index for given meta info.

    Parameters
    ----------
    material_index
        table mapping material mnemonics to material number and density
    mnemonic
        material label from the STP-path
    path
        ... for diagnostics

    Returns
    -------
    density and material
    """
    try:
        material_numbers = material_index["number"]
        material_item = None if material_numbers is None else material_numbers.loc[mnemonic]
        material_number = 0 if material_item is None else material_item.item()
    except KeyError:
        msg = (
            f"The mnemonic {mnemonic or ''!r} "
            "is not specified in the material index. "
            f"See the STP path: {path}"
        )
        raise KeyError(msg) from None
    if material_number > 0:
        densities = material_index["density"]
        if densities is None:
            raise ValueError
        density = densities.loc[mnemonic]
        if np.isnan(density):
            msg = f"The density for mnemonic {mnemonic or ''!r} is not specified in the material index."
            raise ValueError(msg)
        if density < 0.0:
            msg = f"The density for mnemonic {mnemonic or ''!r} in the material index is to be positive."
            raise ValueError(msg)
    else:
        density = 0.0
    return density, material_number


def extract_meta_info_from_path(path: str) -> MetaInfoCollector:
    """Extract the lowest tags from an STP path.

    Parameters
    ----------
    path
        to body which may contain ``m-... f-... r-...`` tags

    Returns
    -------
    Collected meta info map.
    """
    meta_info = MetaInfoCollector()
    found = _META_PATTERN.findall(path)
    if found:
        for meta in found:
            meta_info.update(_extract_meta_info(meta, path))
    return meta_info


def _extract_meta_info(meta: str, path: str) -> dict[str, str]:
    try:
        return dict(_create_pair(t) for t in meta.split())
    except ValueError as _ex:
        msg = f"On path {path}"
        raise ValueError(msg) from _ex


def _create_pair(meta_part: str) -> tuple[str, str]:
    a, b = meta_part.split("-", maxsplit=1)
    return a, b
