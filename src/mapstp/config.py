"""Configuration tools."""
from __future__ import annotations

from typing import Any, Callable, TypeVar

from os import environ

_T = TypeVar("_T")


def env(key, converter: Callable[[str], Any] | None = None, default=None):  # noqa: ANN201
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

    inp = environ[key]

    converter = _extend_converter(converter)

    try:
        return converter(inp)
    except ValueError as exception:
        raise ValueError(
            f"Invalid environment variable {key!r}: "
            f"conversion {converter.__name__}({inp}) failed.",
        ) from exception


def _extend_converter(converter: Callable[[str], Any] | None) -> Callable[[str], Any]:
    if converter is None or converter == str:
        return _identity

    if converter == bool:
        return _make_bool

    return converter


def _identity(val: _T) -> _T:
    return val


def _make_bool(inp: str) -> bool:
    inp = inp.lower()
    if inp in ["1", "true", "yes", "y", "ok", "on"]:
        return True
    if inp in ["0", "false", "no", "n", "nok", "off"]:
        return False
    raise ValueError(f"expected a boolean equivalent, found {inp!r}")
