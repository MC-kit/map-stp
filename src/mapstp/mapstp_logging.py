# noinspection GrazieInspection
"""Logging configuration code.

The mapstp CLI application uses Rich for human-readable console logging, and eliot for structured file logging.
The mapstp library uses standard logging.

.. note::

    By default, logging is disabled, if ``mapstp`` is used as library.
    To enable it, you can either use :func:`init_logging`,
    which is used in CLI module :mod:`__main__`.
    Or provide own initialization for ``mapstp`` logger.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import logging
import sys

from pathlib import Path

import cyclopts

from eliot import to_file
from eliot.stdlib import EliotHandler
from rich.logging import RichHandler
from rich.traceback import install

if TYPE_CHECKING:
    from rich.console import Console

NAME: Final[str] = "mapstp"
PREFIX: Final[Path] = Path(NAME)


def init_logging(
    console: Console,
    *,
    eliot_log: Path | None = None,
    console_log_level: str = "INFO",
) -> None:
    """Init logging using Rich and eliot.

    Parameters
    ----------
    console
        ... to use for logging
    eliot_log
        file for structured eliot logging, optional
    console_log_level
        logging level for console logging
    """
    # Use Rich as the default traceback handler for all uncaught exceptions
    install(show_locals=True)
    logging.getLogger(NAME).disabled = False
    logging.basicConfig(
        level=console_log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, rich_tracebacks=True, tracebacks_suppress=[cyclopts])
        ],
    )
    if not eliot_log and "pytest" not in sys.modules:
        eliot_log = PREFIX.with_suffix(".log")  # pragma: no cover
    if eliot_log:  # pragma: no cover
        to_file(eliot_log.open(mode="a", encoding="utf8"))
        logging.getLogger(NAME).addHandler(EliotHandler())


def get_logger(suffix: str | None = None) -> logging.Logger:
    """Get the package specific logger.

    Parameters
    ----------
    suffix
        The requested logger name, optional

    Returns
    -------
    The logger for name prepended with the package name, if provided,
    otherwise the root mapstp logger
    """
    return logging.getLogger(NAME if suffix is None else NAME + "." + suffix)


# disable logging, if mapstp is used as a library
logging.getLogger(NAME).disabled = True
