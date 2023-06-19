from __future__ import annotations

import pytest

from mapstp.utils.re import CARD_PATTERN


@pytest.mark.parametrize(
    "text,expected",
    [
        ("CUT ...", "card"),
        ("c cut ...", "comment"),
    ],
)
def test_test_card_pattern(text, expected):
    match = CARD_PATTERN.search(text)
    assert match is not None
    assert match.lastgroup == expected
