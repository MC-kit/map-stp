"""Code to load materials index."""
from typing import Optional

from pathlib import Path

import pandas as pd

from mapstp.utils.resource import path_resolver

PACKAGE_DATA = path_resolver("mapstp")("data")


def load_materials_index(materials_index: Optional[str] = None) -> pd.DataFrame:
    """Load material index from file.

    Args:
        materials_index: file name of index to load,
                         if not provided, uses data/default-material-index.xlsx

    Note:
        Validation of material index input values is postponed to usage of defined mnemonics.
        The input file may contain 'missed' data for mnemonics in design phase,
        until the mnemonics are actually used.

    Returns:
        DataFrame with columns mnemonic, number of material, density
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
        sheet_name=0,  # Use the first sheet, regardless of its name.
        usecols=["mnemonic", "number", "eff.density, g/cm3"],
        converters={"number": int, "eff.density, g/cm3": float},
        engine="openpyxl",
    )
    materials = materials.loc[materials["mnemonic"].notnull()]
    materials.rename(columns={"eff.density, g/cm3": "density"}, inplace=True)
    materials.set_index(keys="mnemonic", inplace=True)
    return materials
