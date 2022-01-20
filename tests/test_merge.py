import mapstp.merge as m
import pytest

from mapstp.utils.io import find_first_cell_number


def test_merger(data):
    sections = m.read_mcnp_sections(data / "test3.i")
    assert sections.cells is not None


def test_find_first_cell_number(data):
    mcnp = data / "test-extract-info.i"
    actual = find_first_cell_number(mcnp)
    assert actual == 2000


if __name__ == "__main__":
    pytest.main()
