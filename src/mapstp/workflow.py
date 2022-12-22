"""The module contains typical workflow methods and base methods for them.

Use imported methods to organize other workflows in notebooks or dependant packages.
Check the methods defined here as templates for other workflows.

"""
from typing import List, Tuple

from logging import getLogger
from pathlib import Path

import pandas as pd

from mapstp.extract_info import extract_path_info
from mapstp.materials_index import load_materials_index
from mapstp.stp_parser import parse_path
from mapstp.tree import create_bodies_paths


def create_path_info(
    materials_index: str, stp: str
) -> Tuple[List[List[str]], pd.DataFrame]:
    """Join information from materials index and stp paths to table.

    Args:
        materials_index: file name of materials index file.
        stp: file name of stp file.

    Returns:
        collected paths from the stp file
        table with joined information
    """
    logger = getLogger()
    _materials_index = load_materials_index(materials_index)
    logger.info("Loaded material index from {}", materials_index)
    _stp = Path(stp)
    products, links = parse_path(_stp)
    logger.info("Loaded STP from {}", stp)
    paths = create_bodies_paths(products, links)
    path_info = extract_path_info(paths, _materials_index)
    return paths, path_info
