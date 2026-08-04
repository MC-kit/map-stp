from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import pytest

import mapstp.merge as m
from mapstp.exceptions import PathInfoError
from mapstp.utils import read_mcnp_sections

if TYPE_CHECKING:
    from pathlib import Path


def test_merger(data: Path) -> None:
    sections = read_mcnp_sections(data / "test3.i", encoding="cp1251")
    assert sections.cells is not None


@pytest.mark.parametrize(
    "number,density,factor,expected",
    [
        (1, 7.93, pd.NA, (1, 7.93)),
        (1, 7.93, np.nan, (1, 7.93)),
        (1, 2.0, 2.0, (1, 4.0)),
    ],
)
def test_extract_number_and_density(number: int, density: float, factor: float, expected: tuple[int, float]) -> None:
    ndf_table = pd.DataFrame.from_records(
        data=[(number, density, factor)],
        columns=["material_number", "density", "factor"],
    )
    actual = m.extract_number_and_density(0, ndf_table)
    assert expected == actual


@pytest.mark.parametrize(
    "material_number,density,factor,exception",
    [
        (-1, 7.93, pd.NA, PathInfoError),
        (1, -7.93, np.nan, PathInfoError),
        (1, 2.0, -2.0, PathInfoError),
    ],
)
def test_extract_number_and_density_bad_path(
    material_number: int, density: float, factor: float, exception: type[Exception]
) -> None:
    ndf_table = pd.DataFrame.from_records(
        data=[(material_number, density, factor)],
        columns=["material_number", "density", "factor"],
    )
    with pytest.raises(exception):
        m.extract_number_and_density(0, ndf_table)


if __name__ == "__main__":
    pytest.main()
