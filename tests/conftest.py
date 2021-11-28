from pathlib import Path

import pandas as pd
import pytest

from mapstp.materials_index import load_materials_index
from mapstp.utils.resource import path_resolver


@pytest.fixture(scope="session")
def data() -> Path:
    return path_resolver("tests")("data")


@pytest.fixture(scope="session")
def materials() -> pd.DataFrame:
    return load_materials_index()
