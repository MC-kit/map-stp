import mapstp.merge as m
import pytest


def test_merger(data):
    sections = m.read_mcnp_sections(data / "test3.i")
    assert sections.cells is not None


if __name__ == "__main__":
    pytest.main()
