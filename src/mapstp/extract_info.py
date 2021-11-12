"""Extract meta information from paths given in an STP file."""
import re

import pandas as pd

# TODO dvp: make meta pattern configurable via command line or configuration file

_META_PATTERN = re.compile(".*\\[(?P<meta>[^]]+)]$")


def extract_info(paths, materials: pd.DataFrame) -> pd.DataFrame:
    def records():
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
                    except ValueError as x:
                        raise ValueError(f"On path {path} part #{i}: {part}") from x
                    mnemonic = pars.get("m", mnemonic)
                    factor = pars.get("f", factor)
                    rwcl = pars.get("r", rwcl)
            if mnemonic:
                number = int(
                    materials.loc[mnemonic]["number"]
                )  # TODO dvp: check why type of number became float
                density = materials.loc[mnemonic]["density"]
            else:
                number = density = None
            if factor:
                factor = float(factor)
            yield number, density, factor, rwcl

    df = pd.DataFrame.from_records(
        records(),
        columns="number density factor rwcl".split(),
    )
    return df
