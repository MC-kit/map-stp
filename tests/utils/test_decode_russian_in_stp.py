"""TODO..."""

from __future__ import annotations

import pytest

from mapstp.utils.decode_russian_in_stp import decode_russian


@pytest.mark.parametrize(
    "inp, expected",
    [("\\X2\\04220432043504400434043E0435\\X0\\ \\X2\\04420435043B043E\\X0\\", "Твердое тело")],
)
def test_decode_russian(inp, expected):
    assert expected == decode_russian(inp)


if __name__ == "__main__":
    pytest.main()
