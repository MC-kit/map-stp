from pathlib import Path

import pytest

from mapstp.utils.resource import path_resolver


@pytest.fixture(scope="session")
def data() -> Path:
    return path_resolver("tests")("data")
