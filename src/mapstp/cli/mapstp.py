from typing import Optional

from dataclasses import dataclass
from pathlib import Path

import click
import mapstp.meta as meta

from mapstp.core import create_excel, create_stp_comments

# from .logging import logger
from mapstp.utils.io import can_override

# from click_loguru import ClickLoguru
from mapstp.utils.re import CELL_START_PATTERN


def find_first_cell_number(mcnp):
    _mcnp = Path(mcnp)
    with _mcnp.open(encoding="cp1251") as stream:
        for line in stream:
            match = CELL_START_PATTERN.search(line)
            if match:
                cell_number = int(line[: match.end()].split()[0])
                return cell_number
    raise ValueError(f"Cells with material 0 are not found in {mcnp}. Is it MCNP file?")


def correct_start_cell_number(start_cell_number: Optional[int], mcnp: Optional[str]):
    if not start_cell_number:
        if not mcnp:
            start_cell_number = 1
        else:
            start_cell_number = find_first_cell_number(mcnp)
    return start_cell_number


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

# TODO dvp: add customized configuring from a configuration toml-file.


@dataclass
class Config:
    override: bool = False


# @click_loguru.logging_options
# @click.group(help=meta.__summary__, name=NAME)
@click.command(help=meta.__summary__, name=NAME)
# @click_loguru.init_logger()
# @click_loguru.stash_subcommand()
@click.option(
    "--override/--no-override",
    default=False,
    help="Override existing files, (default: no)",
)
@click.option(
    "--output",
    "-o",
    metavar="<output>",
    type=click.Path(dir_okay=False),
    required=False,
    help="File to write the MCNP with marked cells (default: stdout)",
)
@click.option(
    "--excel",
    "-e",
    metavar="<excel-file>",
    type=click.Path(dir_okay=False),
    required=False,
    help="Excel file to write the component paths",
)
@click.option(
    "--materials-index",
    "-m",
    metavar="<materials-index-file>",
    type=click.Path(dir_okay=False, exists=True),
    required=False,
    help="Excel file containing materials mnemonics and corresponding references for MCNP model.",
)
@click.option(
    "--separator",
    metavar="<separator>",
    type=click.STRING,
    default="/",
    help="String to separate components in the STP path",
)
@click.option(
    "--start-cell-number",
    metavar="<number>",
    type=click.INT,
    required=False,
    help="Number to start cell numbering in the Excel file "
    "(default: the first cell number in `mcnp` file, if specified, otherwise 1)",
)
@click.argument("stp", metavar="<stp-file>", type=click.Path(exists=True))
@click.argument("mcnp", metavar="<mcnp-file>", type=click.Path(exists=True))
@click.version_option(VERSION, prog_name=NAME)
# @logger.catch(reraise=True)
@click.pass_context
# ctx, verbose: bool, quiet: bool, logfile: bool, profile_mem: bool, override: bool
def mapstp(
    ctx,
    override: bool,
    output,
    excel,
    materials_index,
    separator,
    start_cell_number,
    stp,
    mcnp,
) -> None:

    # if quiet:
    #     logger.level("WARNING")
    # if verbose:
    #     logger.level("TRACE")
    # logger.info("Running {}", NAME)
    # logger.debug("Working dir {}", Path(".").absolute())

    #
    cfg = ctx.ensure_object(Config)
    # obj["DEBUG"] = debug
    cfg.override = override
    _stp = Path(stp)
    _mcnp = Path(mcnp)
    products, graph, paths, materials, path_info = create_stp_comments(
        override, output, _stp, _mcnp, materials_index, separator
    )
    if excel:
        start_cell_number = correct_start_cell_number(start_cell_number, mcnp)
        _excel = Path(excel)
        can_override(_excel, override)
        create_excel(_excel, paths, path_info, separator, start_cell_number)


# TODO dvp: handle override option


if __name__ == "__main__":
    mapstp()
