"""Extract meta information from paths given in an STP file."""
from typing import Any, Iterable, Tuple

import re

import pandas as pd

# TODO dvp: make meta pattern configurable via command line or configuration file

_META_PATTERN = re.compile(".*\\[(?P<meta>[^]]+)]$")


def extract_path_info(
    paths: Iterable[Iterable[str]], mnemonic_table: pd.DataFrame
) -> pd.DataFrame:
    """Extract meta information from `paths` and associate corresponding data with each path.

    Args:
        paths: STP paths
        mnemonic_table: mnemonic-material-density lookup table

    Returns:
        Table with material `number`, `density`, applied correction `factor`,
        and `rwcl label corresponding to every path in paths
    """

    def _records() -> Tuple[int, float, float, Any]:
        for path in paths:
            mnemonic = None
            factor = None
            rwcl = None
            for i, part in enumerate(path):
                match = _META_PATTERN.match(part)
                if match:
                    meta = match["meta"]
                    try:
                        pars = dict(map(lambda x: x.split("-", 1), meta.split()))
                    except ValueError as _ex:
                        raise ValueError(f"On path {path} part #{i}: {part}") from _ex
                    mnemonic = pars.get("m", mnemonic)
                    if mnemonic == "void":
                        # all subsequent components in the STP tree are void,
                        # except linked ones, if any
                        mnemonic = None
                        factor = None
                    else:
                        factor = pars.get("f", factor)
                    rwcl = pars.get("r", rwcl)
            if mnemonic:
                number = int(
                    mnemonic_table.loc[mnemonic]["number"]
                )  # TODO dvp: check why type of number became float
                density = mnemonic_table.loc[mnemonic]["density"]
            else:
                number = density = None
            if factor:
                factor = float(factor)
            yield number, density, factor, rwcl

    df = pd.DataFrame.from_records(
        _records(),
        columns="number density factor rwcl".split(),
    )
    return df
