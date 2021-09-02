from dataclasses import dataclass
from pathlib import Path

import click
import mapstp.meta as meta

# from click_loguru import ClickLoguru

# from .logging import logger

NAME = meta.__title__
VERSION = meta.__version__
# LOG_FILE_RETENTION = 3
# NO_LEVEL_BELOW = 30
#
#
# def stderr_log_format_func(msgdict):
#     """Do level-sensitive formatting.
#
#     Just a copy from click-loguru so far."""
#
#     if msgdict["level"].no < NO_LEVEL_BELOW:
#         return "<level>{message}</level>\n"
#     return "<level>{level}</level>: <level>{message}</level>\n"
#
#
# click_loguru = ClickLoguru(
#     NAME,
#     VERSION,
#     stderr_format_func=stderr_log_format_func,
#     retention=LOG_FILE_RETENTION,
#     log_dir_parent=".logs",
#     timer_log_level="info",
# )
# context = {}


# @click_loguru.logging_options
# @click.group(help=meta.__summary__, name=NAME)
@click.command(help=meta.__summary__, name=NAME)
# @click_loguru.init_logger()
# @click_loguru.stash_subcommand()
@click.option("--override/--no-override", default=False)
@click.version_option(VERSION, prog_name=NAME)
# @logger.catch(reraise=True)
@click.pass_context
# ctx, verbose: bool, quiet: bool, logfile: bool, profile_mem: bool, override: bool
def mapstp(ctx, override: bool) -> None:
    # if quiet:
    #     logger.level("WARNING")
    # if verbose:
    #     logger.level("TRACE")
    # logger.info("Running {}", NAME)
    # logger.debug("Working dir {}", Path(".").absolute())

    #
    # TODO dvp: add customized logger configuring from a configuration toml-file.
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below
    # obj = ctx.ensure_object(dict)
    # obj["DEBUG"] = debug
    # context["OVERRIDE"] = override
    assert ctx
    pass


if __name__ == "__main__":
    mapstp()
