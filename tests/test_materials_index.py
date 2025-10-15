from __future__ import annotations

from pathlib import Path

import pytest

from mapstp.materials_index import load_materials_index


def test_load_materials_index_bad_path():
    with pytest.raises(FileNotFoundError):
        load_materials_index(Path("not_existing"))
