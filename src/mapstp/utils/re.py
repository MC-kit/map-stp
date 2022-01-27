"""The regular expressions to be used in various modules."""

import re

CELL_START_PATTERN = re.compile(r"^\s{0,5}\d+\s+0")
"""Line starts with number followed with 0."""

CELLS_END_PATTERN = re.compile(r"^\s*$")
"""Empty line.

Separates sections in MCNP file.
"""

MATERIAL_PATTERN = re.compile(r"^\s{0,4}[mM](?P<material>\d+)")
"""Start of an MCNP card with material specification."""

CARD_PATTERN = re.compile(r"^\s{0,4}(?:(?P<comment>[cC]\s)|(?P<card>\w+))")
"""Start of MCNP line with comment or any card."""

MCNP_SECTIONS_SEPARATOR_PATTERN = re.compile(r"^\s*$", re.MULTILINE)

#
# Advise: check regular expressions on: https://pythex.org/
#
