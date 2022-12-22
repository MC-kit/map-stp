"""Intercept log messages from the used libraries and pass them to `loguru`.

See https://github.com/Delgan/loguru

"""
from typing import Final, Optional

import logging
import sys

from pathlib import Path

from loguru import logger
from mapstp.config import env

# class PropagateHandler(logging.Handler):
#     """Send events from loguru to standard logging"""
#     def emit(self, record):
#         logging.getLogger(record.name).handle(record)
#
#
# logger.add(PropagateHandler(), format="{message}")


class InterceptHandler(logging.Handler):
    """Send events from standard logging to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """See :meth:`logging.Handler.emit`.

        Args:
            record: data to log
        """
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = logging.getLevelName(record.levelno)

        # Find caller from where originated the logged message
        frame = logging.currentframe()
        depth = 2
        while frame.f_code.co_filename == logging.__file__:  # pragma: no cover
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


log = logging.getLogger()
# log.setLevel(0)
log.addHandler(InterceptHandler())
# logging.basicConfig(handlers=[InterceptHandler()], level=0, style='{')

# from loguru._defaults.py
# "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
# "<level>{level: <8}</level> | "
# "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",

MAPSTP_CONSOLE_LOG_FORMAT: Final[str] = env(
    "MAPSTP_CONSOLE_LOG_FORMAT",
    default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>",
)
MAPSTP_FILE_LOG_PATH: Final[Path] = env(
    "MAPSTP_FILE_LOG_PATH", converter=Path, default="mapstp.log"
)


def init_logger(
    *,
    stderr_format: Optional[str] = MAPSTP_CONSOLE_LOG_FORMAT,
    log_path: Optional[Path] = MAPSTP_FILE_LOG_PATH,
) -> None:
    """Configure logger with given parameters.

    Args:
        stderr_format: log message format for stderr handler, if None, no stderr logging.
        log_path: path to file for logging, if None, no file logging.
    """
    logger.remove()
    if stderr_format:
        logger.add(
            sys.stderr,
            format=stderr_format,
            level="INFO",
            backtrace=False,
            diagnose=False,
        )
    if log_path:
        logger.add(log_path, rotation="100 MB", backtrace=True, diagnose=True)
