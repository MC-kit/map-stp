import numpy as np
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
    _expected = pd.DataFrame.from_records(expected, columns=["number", "density", "factor", "rwcl"])
    actual = extract_path_info(paths, materials)
    isna = actual.isna()
    assert (isna == _expected.isna()).all(axis=None), msg
    assert (actual == _expected).mask(isna).all(axis=None), msg


@pytest.mark.parametrize(
    "paths, exception, msg",
    [
        (
            [["aaa [m-Unknown]", "bbb", "ccc0"]],
            KeyError,
            "The mnemonic 'Unknown' is not specified in the material index. "
            "See the STP path: aaa [m-Unknown]/bbb/ccc0",
        ),
    ],
)
def test_extract_info_with_missed_material(materials, paths, exception, msg):
    with pytest.raises(exception) as x:
        extract_path_info(paths, materials)
        assert x.type is exception
        assert x.value == msg


@pytest.mark.parametrize(
    "paths, exception, msg",
    [
        (
            [["aaa [m-LH]", "bbb", "ccc0"]],
            ValueError,
            "The density for mnemonic 'LH' is not specified in the material index.",
        ),
    ],
)
def test_extract_info_with_missed_density(materials, paths, exception, msg):
    materials_without_density = materials.loc[["LH"]]
    materials_without_density.density = np.NaN
    with pytest.raises(exception) as x:
        extract_path_info(paths, materials_without_density)
        assert x.type is exception
        assert x.value == msg


@pytest.mark.parametrize(
    "paths, exception, msg",
    [
        (
            [["aaa [m-LH]", "bbb", "ccc0"]],
            ValueError,
            "The density for mnemonic 'LH' in the material index is to be positive.",
        ),
    ],
)
def test_extract_info_with_negative_density(materials, paths, exception, msg):
    materials_with_negative_density = materials.loc[["LH"]]
    materials_with_negative_density.density = -1.0
    with pytest.raises(exception) as x:
        extract_path_info(paths, materials_with_negative_density)
        assert x.type is exception
        assert x.value == msg


if __name__ == "__main__":
    pytest.main()
