from typing import Any, Type

from os import environ


def env(key: str, type_: Type[Any] = str, default=None):
    if key not in environ:
        return default

    val = environ[key]

    if type_ == str:
        return val

    if type_ == bool:
        val = val.lower()
        if val in ["1", "true", "yes", "y", "ok", "on"]:
            return True
        if val in ["0", "false", "no", "n", "nok", "off"]:
            return False
        raise ValueError(
            f"Invalid environment variable '{key}': expected a boolean, found '{val}'"
        )

    if type_ == int:
        try:
            return int(val)
        except ValueError:
            raise ValueError(
                f"Invalid environment variable '{key}': expected an integer, found '{val}'"
            ) from None

    if type_ == float:
        try:
            return float(val)
        except ValueError:
            raise ValueError(
                f"Invalid environment variable '{key}': expected a float, found '{val}'"
            ) from None

    try:
        return type_(val)
    except ValueError:
        raise ValueError(
            f"Invalid environment variable '{key}': conversion {type_.__name__}({val}) failed."
        ) from None


# MAPSTP_AUTOINIT: Final[bool] = env("MAPSTP_AUTOINIT", bool, True)
