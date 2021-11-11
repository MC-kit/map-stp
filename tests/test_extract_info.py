import pandas as pd
import pytest

from mapstp.extract_info import extract_info, load_materials_index


@pytest.fixture(scope="session")
def materials():
    return load_materials_index()


def test_load_materials_index(materials):
    actual = materials
    assert (actual.columns == ["number", "density"]).all()
    number = actual.loc["LH"]["number"]
    assert number == 2


@pytest.mark.parametrize(
    "paths, expected",
    [
        ([["aaa [m:LH]", "bbb", "ccc0"]], [(2, 0.14822, None, None)]),
        ([["aaa [m:LH]", "bbb[f:0.9]", "ccc0"]], [(2, 0.14822, 0.9, None)]),
        (
            [["aaa [m:LH]", "bbb[f:0.99]", "ccc0[r:PBS55]"]],
            [(2, 0.14822, 0.99, "PBS55")],
        ),
    ],
)
def test_extract_info(materials, paths, expected):
    _expected = pd.DataFrame.from_records(
        expected, columns="number density factor rwcl".split()
    )
    actual = extract_info(paths, materials)
    isnull = actual.isnull()
    assert (isnull == _expected.isnull()).all(axis=None)
    assert (actual == _expected).mask(isnull).all(axis=None)


if __name__ == "__main__":
    pytest.main()
