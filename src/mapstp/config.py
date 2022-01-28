"""Configuration tools."""

from typing import Any, Type

from os import environ


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


def env(key: str, type_: Type[Any] = str, default: Any = None) -> Any:
    """Retrieve environment variable and convert to specified type with proper diagnostics.

    Args:
        key: environment variable name
        type_: type to convert to
        default: value to use, if there are no variable with the name `key`

    Returns:
        Loaded value converted to `type_` or default.

    Raises:
        ValueError: if conversion is not possible.
    """
    if key not in environ:
        return default

    val = environ[key]

    if type_ == str:
        return val

    if type_ == bool:
        return _make_bool(key, val)

    if type_ == int:
        return _make_int(key, val)

    if type_ == float:
        return _make_float(key, val)

    try:
        return type_(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': conversion {type_.__name__}({val}) failed."
        ) from None


# MAPSTP_AUTOINIT: Final[bool] = env("MAPSTP_AUTOINIT", bool, True)
