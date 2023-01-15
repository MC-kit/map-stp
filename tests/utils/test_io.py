import pytest

from mapstp.utils.io import find_first_cell_number, read_mcnp_sections


def test_find_first_cell_number(data):
    mcnp = data / "test-extract-info.i"
    actual = find_first_cell_number(mcnp)
    assert actual == 2000


def test_find_first_cell_number_bad_paths(data):
    mcnp = data / "test1.stp"
    with pytest.raises(ValueError):
        find_first_cell_number(mcnp)


def test_read_mcnp_sections(data, tmp_path):
    mcnp = data / "test1.i"
    sections = read_mcnp_sections(mcnp)
    assert sections.cells and sections.surfaces and sections.cards and sections.remainder is None
    tmp = tmp_path / "test-with-cells-and-surfaces-only.i"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("\n\n".join([sections.cells, sections.surfaces]))
    sections = read_mcnp_sections(tmp)
    assert (
        sections.cells
        and sections.surfaces
        and sections.cards is None
        and sections.remainder is None
    )


def test_read_mcnp_sections_with_remainder(data, tmp_path):
    mcnp = data / "test1.i"
    text = mcnp.read_text()
    tmp = tmp_path / "test.i"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("\n\n".join([text, "remainder\nabc"]))
    sections = read_mcnp_sections(tmp)
    assert (
        sections.cells
        and sections.surfaces
        and sections.cards
        and sections.remainder == "remainder\nabc"
    )


def test_read_mcnp_sections_with_empty_remainder(data, tmp_path):
    mcnp = data / "test1.i"
    text = mcnp.read_text()
    tmp = tmp_path / "test.i"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("\n\n".join([text, "\n" * 2]))
    sections = read_mcnp_sections(tmp)
    assert sections.cells and sections.surfaces and sections.cards and sections.remainder is None
