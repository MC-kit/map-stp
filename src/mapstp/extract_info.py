"""Extract meta information from paths given in an STP file."""
from typing import Dict, Generator, List, Optional, Tuple

import re

from dataclasses import dataclass

import pandas as pd

# TODO dvp: make meta pattern configurable via command line or configuration file

_META_PATTERN = re.compile(r".*\[(?P<meta>[^]]+)]")


@dataclass
class _MetaInfo:
    mnemonic: Optional[str] = None
    factor: Optional[float] = None
    rwcl: Optional[str] = None

    def update(self, pars: Dict[str, str]) -> None:
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


def extract_path_info(
    paths: List[List[str]], mnemonic_table: pd.DataFrame
) -> pd.DataFrame:
    """Extract meta information from `paths` and associate corresponding data with each path.

    Args:
        paths: STP paths
        mnemonic_table: mnemonic-material-density lookup table

    Returns:
        Table with material `number`, `density`, applied correction `factor`,
        and `rwcl label corresponding to every path in paths
    """

    def _records() -> Generator[
        Tuple[Optional[int], Optional[float], Optional[float], Optional[str]],
        None,
        None,
    ]:
        for path in paths:
            meta_info = _MetaInfo()
            for i, part in enumerate(path):
                match = _META_PATTERN.match(part)
                if match:
                    pars = _extract_meta_info(i, match, part, path)
                    meta_info.update(pars)
            if meta_info.mnemonic:
                number: Optional[int] = int(
                    mnemonic_table.loc[meta_info.mnemonic]["number"]
                )  # TODO dvp: check why type of number became float
                density: Optional[float] = mnemonic_table.loc[meta_info.mnemonic][
                    "density"
                ]
            else:
                number = density = None
            yield number, density, meta_info.factor, meta_info.rwcl

    df = pd.DataFrame.from_records(
        _records(),
        columns="number density factor rwcl".split(),
    )
    return df


def _extract_meta_info(
    i: int, match: re.Match, part: str, path: List[str]
) -> Dict[str, str]:
    meta = match["meta"]
    try:
        pars: Dict[str, str] = dict(map(_create_pair, meta.split()))
    except ValueError as _ex:
        raise ValueError(f"On path {path} part #{i}: {part}") from _ex
    return pars


def _create_pair(x: str) -> Tuple[str, str]:
    a, b = x.split("-", 1)  # type: str, str
    return a, b
