import re

CELL_START_PATTERN = re.compile(r"^\s{0,5}\d+\s+0")
"""Line starts with number followed with 0."""

CELLS_END_PATTERN = re.compile(r"^\s*$")
"""Empty line."""
