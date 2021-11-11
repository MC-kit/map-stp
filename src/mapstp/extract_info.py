"""Extract meta information from paths given in an STP file."""

import re

from pathlib import Path

import pandas as pd

from mapstp.utils.resource import path_resolver

PACKAGE_DATA = path_resolver("mapstp")("data")


def load_materials_index(materials_index: str = None) -> pd.DataFrame:
    """Load material index from file.

    Args:
        materials_index: file name of index to load,
                         if not provided, uses data/default-material-index.xlsx

    Returns:
        DataFrame with with columns mnemonic, number of material, density
        with omitted rows, where mnemonic is not specified.

    Raises:
        FileNotFoundError: if the file `materials_index` doesn't exist.

    """
    if materials_index is None:
        p = PACKAGE_DATA / "default-material-index.xlsx"
    else:
        p = Path(materials_index)
    if not p.exists():
        raise FileNotFoundError(p)
    materials = pd.read_excel(
        p,
        usecols=["mnemonic", "number", "eff.density, g/cm3"],
        converters={"number": int},
    )
    materials = materials.loc[materials["mnemonic"].notnull()]
    materials.rename(columns={"eff.density, g/cm3": "density"}, inplace=True)
    materials.set_index(keys="mnemonic", inplace=True)
    return materials


# TODO dvp: make meta pattern configurable via command line or configuration file

_META_PATTERN = re.compile(".*\\[(?P<meta>[^]]+)]$")


def extract_info(paths, materials: pd.DataFrame) -> pd.DataFrame:
    def records():
        for path in paths:
            mnemonic = None
            factor = None
            rwcl = None
            for part in path:
                match = _META_PATTERN.match(part)
                if match:
                    meta = match["meta"]
                    pars = dict(map(lambda x: x.split(":"), meta.split()))
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
