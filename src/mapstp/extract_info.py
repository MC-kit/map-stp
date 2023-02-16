"""Extract meta information from paths given in an STP file."""
from typing import Dict, Generator, List, Optional, Tuple

import re

from dataclasses import dataclass

import numpy as np

import pandas as pd

_META_PATTERN = re.compile(r".*\[(?P<meta>[^]]+)]")


@dataclass
class _MetaInfoCollector:
    mnemonic: Optional[str] = None
    factor: Optional[float] = None
    rwcl: Optional[str] = None

    def update(self, pars: Dict[str, str]) -> None:
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


def extract_path_info(paths: List[List[str]], material_index: pd.DataFrame) -> pd.DataFrame:
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
        columns=["number", "density", "factor", "rwcl"],
    )


def _records(
    paths, material_index
) -> Generator[Tuple[Optional[int], Optional[float], Optional[float], Optional[str]], None, None]:
    for path in paths:
        meta_info = _extract_meta_info_from_path(path)
        if meta_info.mnemonic:
            density, number = _define_material_number_and_density(material_index, meta_info, path)
        else:
            number = density = None
        yield number, density, meta_info.factor, meta_info.rwcl


def _define_material_number_and_density(
    material_index, meta_info, path
) -> Tuple[Optional[float], Optional[int]]:
    try:
        number: Optional[int] = int(material_index.loc[meta_info.mnemonic]["number"])
    except KeyError:
        raise KeyError(
            f"The mnemonic {meta_info.mnemonic!r} "
            "is not specified in the material index. "
            f"See the STP path: {'/'.join(path)}"
        ) from None
    density = material_index.loc[meta_info.mnemonic]["density"]
    if np.isnan(density):
        raise ValueError(
            f"The density for mnemonic {meta_info.mnemonic!r} "
            "is not specified in the material index."
        )
    if density < 0.0:
        raise ValueError(
            f"The density for mnemonic {meta_info.mnemonic!r} "
            "in the material index is to be positive."
        )
    return density, number


def _extract_meta_info_from_path(path) -> _MetaInfoCollector:
    meta_info = _MetaInfoCollector()
    for i, part in enumerate(path):
        match = _META_PATTERN.match(part)
        if match:
            pars = _extract_meta_info(i, match, part, path)
            meta_info.update(pars)
    return meta_info


def _extract_meta_info(i: int, match: re.Match, part: str, path: List[str]) -> Dict[str, str]:
    meta = match["meta"]
    try:
        pars: Dict[str, str] = dict(map(_create_pair, meta.split()))
    except ValueError as _ex:
        raise ValueError(f"On path {path} part #{i}: {part}") from _ex
    return pars


def _create_pair(x: str) -> Tuple[str, str]:
    a, b = x.split("-", 1)  # type: str, str
    return a, b
