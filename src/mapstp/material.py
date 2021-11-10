# from typing import Dict
import re

from pathlib import Path

import numpy as np
import pandas as pd

from mapstp.utils.resource import path_resolver

PACKAGE_DATA = path_resolver("mapstp")("data")


def load_materials_index(materials_index: str = None) -> pd.DataFrame:
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


_META_PATTERN = re.compile(r".*\[(?P<mnemonic>[^|]*)(?:\|(?P<factor>[^|]+))?]$")


def load_materials(paths, materials_index: str = None):
    materials = load_materials_index(materials_index)

    res = []
    for p in paths:
        mnemonic = None
        factor = None
        for w in p:
            match = _META_PATTERN.match(w)
            if match:
                gd = match.groupdict()
                t = gd.get("mnemonic", mnemonic)
                if t != "":
                    mnemonic = t
                factor = gd.get("factor", factor)
        if mnemonic:
            number = int(
                materials.loc[mnemonic]["number"]
            )  # TODO dvp: check why type of number became float
            density = materials.loc[mnemonic]["density"]
        else:
            number = density = None
        if factor:
            factor = float(factor)
        item = (number, density, factor)
        res.append(item)
    return res
