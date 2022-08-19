"""Configuration tools."""
from __future__ import annotations

from typing import TypeVar

from os import environ

_T = TypeVar("_T")


def _make_bool(key: str, val: str) -> bool:
    val = val.lower()
    if val in ["1", "true", "yes", "y", "ok", "on"]:
        return True
    if val in ["0", "false", "no", "n", "nok", "off"]:
        return False
    raise ValueError(
        f"Invalid environment variable '{key}': expected a boolean, found '{val}'"
    )


def _make_int(key: str, val: str) -> int:
    try:
        return int(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': expected an integer, found '{val}'"
        ) from None


def _make_float(key: str, val: str) -> float:
    try:
        return float(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': expected a float, found '{val}'"
        ) from None


def env(key, converter=str, default=None):
    """Retrieve environment variable and convert to specified type with proper diagnostics.

    Args:
        key: environment variable name
        converter: type to convert to
        default: value to use, if there are no variable with the name `key`

    Returns:
        Loaded value converted with `converter` or default.

    Raises:
        ValueError: if conversion is not possible.
    """
    if key not in environ:
        return default

    val = environ[key]

    if converter is None or converter == str:
        return val

    if converter == bool:
        return _make_bool(key, val)

    if converter == int:
        return _make_int(key, val)

    if converter == float:
        return _make_float(key, val)

    try:
        return converter(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': "
            f"conversion {converter.__name__}({val}) failed."
        ) from None
