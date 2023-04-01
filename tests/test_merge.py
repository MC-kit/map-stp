from __future__ import annotations

import numpy as np

import mapstp.merge as m
import pandas as pd
import pytest


def test_merger(data):
    sections = m.read_mcnp_sections(data / "test3.i")
    assert sections.cells is not None


@pytest.mark.parametrize(
    "number,density,factor,expected",
    [
        (1, 7.93, pd.NA, (1, 7.93)),
        (1, 7.93, np.NAN, (1, 7.93)),
        (1, 2.0, 2.0, (1, 4.0)),
    ],
)
def test_extract_number_and_density(number, density, factor, expected):
    ndf_table = pd.DataFrame.from_records(
        data=[(number, density, factor)], columns=["number", "density", "factor"]
    )
    actual = m.extract_number_and_density(0, ndf_table)
    assert expected == actual


@pytest.mark.parametrize(
    "number,density,factor,exception",
    [
        (-1, 7.93, pd.NA, m.PathInfoError),
        (1, -7.93, np.NAN, m.PathInfoError),
        (1, 2.0, -2.0, m.PathInfoError),
    ],
)
def test_extract_number_and_density_bad_path(number, density, factor, exception):
    ndf_table = pd.DataFrame.from_records(
        data=[(number, density, factor)], columns=["number", "density", "factor"]
    )
    with pytest.raises(exception):
        m.extract_number_and_density(0, ndf_table)


if __name__ == "__main__":
    pytest.main()
