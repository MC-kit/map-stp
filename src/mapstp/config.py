from typing import Any, Final, Type

from os import environ


def env(key: str, _type: Type[Any] = str, default=None):
    if key not in environ:
        return default

    val = environ[key]

    if _type == str:
        return val

    if _type == bool:
        val = val.lower()
        if val in ["1", "true", "yes", "y", "ok", "on"]:
            return True
        if val in ["0", "false", "no", "n", "nok", "off"]:
            return False
        raise ValueError(
            f"Invalid environment variable '{key}': expected a boolean, found '{val}'"
        )

    if _type == int:
        try:
            return int(val)
        except ValueError:
            raise ValueError(
                f"Invalid environment variable '{key}': expected an integer, found '{val}'"
            ) from None

    if _type == float:
        try:
            return float(val)
        except ValueError:
            raise ValueError(
                f"Invalid environment variable '{key}': expected a float, found '{val}'"
            ) from None

    try:
        return _type(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': conversion {_type.__name__}({val}) failed."
        ) from None


# MAPSTP_AUTOINIT: Final[bool] = env("MAPSTP_AUTOINIT", bool, True)
