from typing import List

from pathlib import Path

import pandas as pd
import pytest

from mapstp.materials_index import load_materials_index
from mapstp.stp_parser import parse_path
from mapstp.tree import create_bodies_paths
from mapstp.utils.resource import path_resolver


@pytest.fixture(scope="session")
def data() -> Path:
    return path_resolver("tests")("data")


@pytest.fixture(scope="session")
def materials() -> pd.DataFrame:
    return load_materials_index()


@pytest.fixture(scope="session")
def paths_ei(data) -> List[List[str]]:
    _stp = Path(data / "test-extract-info.stp")
    products, links = parse_path(_stp)
    paths = create_bodies_paths(products, links)
    return paths
