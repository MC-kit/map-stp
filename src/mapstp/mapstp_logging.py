"""Logging configuration code.

.. note::

    By default, logging is disabled, if ``mapstp`` is used as library.
    To enable it, you can use :func:`init_logging`,
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

if TYPE_CHECKING:
    from rich.console import Console

NAME: Final[str] = "mapstp"
PREFIX: Final[Path] = Path(NAME)


def init_logging(console: Console, eliot_log: Path | None = None) -> None:
    """Init logging using Rich and eliot.

    Parameters
    ----------
    eliot_log, optional
        file for structured eliot logging
    """
    logging.getLogger("mapstp").disabled = False
    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, rich_tracebacks=True, tracebacks_suppress=[cyclopts])
        ],
    )
    if not eliot_log and "pytest" not in sys.modules:
        eliot_log = PREFIX.with_suffix(".log")
    if eliot_log:
        to_file(eliot_log.open(mode="a"))
        # Add Eliot Handler to root Logger. You may wish to only route specific
        # Loggers to Eliot.
        logging.getLogger().addHandler(EliotHandler())


# disable logging, if mapstp is used as a library
logging.getLogger("mapstp").disabled = True
