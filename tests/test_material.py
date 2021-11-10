import pytest

from mapstp.material import load_materials, load_materials_index


def test_load_materials_index():
    actual = load_materials_index()
    assert (actual.columns == ["number", "density"]).all()
    number = actual.loc["LH"]["number"]
    assert number == 2
    assert isinstance(number, int)


@pytest.mark.parametrize(
    "paths, expected",
    [
        # ([["aaa [LH]", "bbb", "ccc0"]], [(2, 0.14822, None)]),
        ([["aaa [LH]", "bbb[|0.9]", "ccc0"]], [(2, 0.14822, 0.9)]),
    ],
)
def test_load_materials(paths, expected):
    actual = load_materials(paths)
    assert actual == expected


if __name__ == "__main__":
    pytest.main()
