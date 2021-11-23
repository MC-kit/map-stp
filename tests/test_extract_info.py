import pandas as pd
import pytest

from mapstp.extract_info import extract_path_info


def test_load_materials_index(materials):
    actual = materials
    assert (actual.columns == ["number", "density"]).all()
    number = actual.loc["LH"]["number"]
    assert number == 2


@pytest.mark.parametrize(
    "paths, expected, msg",
    [
        (
            [["aaa [m-LH]", "bbb", "ccc0"]],
            [(2, 0.14822, None, None)],
            "Just material (LiH)",
        ),
        (
            [["aaa [m-LH]", "bbb[f-0.9]", "ccc0"]],
            [(2, 0.14822, 0.9, None)],
            "Material and factor",
        ),
        (
            [["aaa [m-LH]", "bbb[f-0.99]", "ccc0[r-PBS55]"]],
            [(2, 0.14822, 0.99, "PBS55")],
            "Material, factor, and RWCL id",
        ),
        (
            [["aaa [m-LH].1", "bbb[f-0.99]", "ccc0[r-PBS55]"]],
            [(2, 0.14822, 0.99, "PBS55")],
            "Should recognize material label, which is not at the end of name.",
        ),
    ],
)
def test_extract_info(materials, paths, expected, msg):
    _expected = pd.DataFrame.from_records(
        expected, columns="number density factor rwcl".split()
    )
    actual = extract_path_info(paths, materials)
    isnull = actual.isnull()
    assert (isnull == _expected.isnull()).all(axis=None), msg
    assert (actual == _expected).mask(isnull).all(axis=None), msg


if __name__ == "__main__":
    pytest.main()
