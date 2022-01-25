from mapstp.utils.io import find_first_cell_number


def test_find_first_cell_number(data):
    mcnp = data / "test-extract-info.i"
    actual = find_first_cell_number(mcnp)
    assert actual == 2000
