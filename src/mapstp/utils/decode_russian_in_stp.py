"""Convert encoded Russian texts in STP branches to string."""

from __future__ import annotations

import re

DECODING_TABLE = {f"{c:04X}": chr(c) for c in range(ord("A"), ord("я") + 1)}
SEARCH_RUSSIAN_RE = re.compile(r"\\X2\\([0-9A-F]+)\\X0\\")


def _replace_stp_encoding(match_result: re.Match[str]) -> str:
    encoded = match_result.group(1)
    split = [encoded[4 * i : 4 * i + 4] for i in range(len(encoded) // 4)]
    decoded = [DECODING_TABLE[code] for code in split]
    return "".join(decoded)


def decode_russian(stp_text: str) -> str:
    """Convert encoded Russian text to unicode string.

    Args:
        stp_text: the text to decode

    Returns:
        Decoded text.
    """
    return re.sub(SEARCH_RUSSIAN_RE, _replace_stp_encoding, stp_text)


__all__ = ["decode_russian"]
