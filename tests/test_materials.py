from __future__ import annotations

import pytest

from mapstp.materials import drop_material_cards, load_materials_map


def test_load_materials_map(data):
    materials = data / "materials-1.txt"
    materials_map = load_materials_map(materials)
    assert len(materials_map) == 2
    assert (
        materials_map[1]
        == """m1   $ pure hydrogen
         1001.31c   0.9999
         1002.31c   0.0001
"""
    )
    assert 400 in materials_map


def test_filter_material_cards(data):
    materials = data / "materials-1.txt"
    filtered_lines = list(
        drop_material_cards(materials.read_text(encoding="cp1251").split("\n"))
    )
    assert len(filtered_lines) == 2
    assert filtered_lines[0] == "c test data"


if __name__ == "__main__":
    pytest.main()
