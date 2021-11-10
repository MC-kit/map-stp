from typing import List

import sys

from dataclasses import dataclass
from pathlib import Path

import click
import mapstp.meta as meta
import pandas as pd

from mapstp.merge import merge_paths
from mapstp.stp_parser import parse_path
from mapstp.tree import create_bodies_paths

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
    type=click.Path(),
    required=False,
    help="File to write the MCNP with marked cells (default: stdout)",
)
@click.option(
    "--excel",
    "-e",
    metavar="<excel-file>",
    type=click.Path(),
    required=False,
    help="Excel file to write the component paths",
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
    default=1,
    help="Number to start cell numbering in the Excel file",
)
@click.argument("stp", metavar="<stp-file>", type=click.Path(exists=True))
@click.argument("mcnp", metavar="<mcnp-file>", type=click.Path(exists=True))
@click.version_option(VERSION, prog_name=NAME)
# @logger.catch(reraise=True)
@click.pass_context
# ctx, verbose: bool, quiet: bool, logfile: bool, profile_mem: bool, override: bool
def mapstp(
    ctx, override: bool, output, excel, separator, start_cell_number, stp, mcnp
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
    products, graph, paths = create_stp_comments(
        override, output, _stp, _mcnp, separator
    )
    if excel:
        _excel = Path(excel)
        create_excel(override, _excel, paths, separator, start_cell_number)


# TODO dvp: handle override option


def create_stp_comments(override, output, stp, mcnp, separator):
    if output:
        p = Path(output)
        if p.exists():
            if not override:
                raise FileExistsError(
                    f"File {p} already exists. Consider --override command line option."
                )
        _output = p.open(mode="w", encoding="cp1251")
    else:
        _output = sys.stdout
    try:
        products, graph = parse_path(stp)
        paths = create_bodies_paths(products, graph)
        merge_paths(_output, paths, mcnp, separator)
        return products, graph, paths
    finally:
        if _output is not sys.stdout:
            _output.close()


def create_excel(
    override, excel: Path, paths: List[List[str]], separator, start_cell_number
) -> None:
    if excel.exists():
        if not override:
            raise FileExistsError(
                f"File {excel} already exists. Consider --override command line option."
            )
    df = pd.DataFrame(
        list(map(lambda x: separator.join(x), paths)),
        index=list(range(start_cell_number, len(paths) + start_cell_number)),
        columns=["STP path"],
    )
    df.index.name = "cell"
    with pd.ExcelWriter(excel) as xlsx:
        df.to_excel(xlsx, sheet_name="Cells")


if __name__ == "__main__":
    mapstp()
