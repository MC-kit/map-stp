"""Application to transfer meta information from STP.

For given STP file creates Excel table with a list
of STP paths to STP components, corresponding to cells
in MCNP model, would it be generated from the STP with SuperMC.

The excel also contains material numbers, densities, correction factors,
and RWCL id. The values can be specified in the names of STP
components as special tags. A tag is denoted with bracket enclosed
specification at the end of component name: "Component name [<spec>]".
The spec may contain space separated entries:
  - m:<mnemonic> - first column in a special material-index.xlxs file.
  - f:<factor>   - float number for density correction factor
  - r:<rwcl>     - any label to categorize the components for RWCL

If MCNP file is also specified as the second `mcnp` argument,
then produces output MCNP file with STP paths inserted
as end of line comments after corresponding cells with prefix
"sep:". The material numbers and densities are set according
to the meta information provided in the STP.
"""
from typing import Dict, List, Optional

from dataclasses import dataclass
from pathlib import Path

import click
import mapstp.meta as meta
import pandas as pd

from mapstp.excel import create_excel
from mapstp.extract_info import extract_path_info
from mapstp.materials import load_materials_map
from mapstp.materials_index import load_materials_index
from mapstp.merge import merge_paths
from mapstp.stp_parser import parse_path
from mapstp.tree import create_bodies_paths
from mapstp.utils.io import can_override, find_first_cell_number, select_output

# from .logging import logger
# from click_loguru import ClickLoguru


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
# def stderr_log_format_func(msg_dict):
#     """Do level-sensitive formatting.
#
#     Just a copy from click-loguru so far."""
#
#     if msg_dict["level"].no < NO_LEVEL_BELOW:
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


_USAGE = f"""
{meta.__summary__}

For given STP file creates Excel table with a list
of STP paths to STP components, corresponding to cells
in MCNP model, would it be generated from the STP with SuperMC.

If MCNP file is also specified as the second `mcnp-file` argument,
then produces output MCNP file with STP paths inserted
as end of line comments after corresponding cells with prefix
"sep:". The material numbers and densities are set according
to the meta information provided in the STP.
"""


# @click_loguru.logging_options
# @click.group(help=meta.__summary__, name=NAME)


@click.command(help=_USAGE, name=NAME)
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
    "--materials",
    metavar="<materials-file>",
    type=click.Path(dir_okay=False, exists=True),
    required=False,
    help="Text file containing MCNP materials specifications."
    "If present, the selected materials present in this file are printed"
    "to the `output` MCNP model, so, it becomes complete valid model",
)
@click.option(
    "--materials-index",
    "-m",
    metavar="<materials-index-file>",
    type=click.Path(dir_okay=False, exists=True),
    required=False,
    help="Excel file containing materials mnemonics and corresponding references for MCNP model "
    "(default: file from the package internal data corresponding to ITER C-model)",
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
@click.argument(
    "stp", metavar="<stp-file>", type=click.Path(dir_okay=False, exists=True)
)
@click.argument(
    "mcnp",
    metavar="[mcnp-file]",
    type=click.Path(dir_okay=False, exists=True),
    required=False,
)
@click.version_option(VERSION, prog_name=NAME)
# @logger.catch(reraise=True)
@click.pass_context
# ctx, verbose: bool, quiet: bool, logfile: bool, profile_mem: bool, override: bool
def mapstp(
    ctx,
    override: bool,
    output,
    excel,
    materials,
    materials_index,
    separator,
    start_cell_number,
    stp,
    mcnp,
) -> None:
    f"""Transfers meta information from STP to MCNP model and Excel.

    Args:
        ctx:
        override:
        output:
        excel:
        materials:
        materials_index:
        separator:
        start_cell_number:
        stp:
        mcnp:

    Returns:

    """
    if not (mcnp or excel):
        raise click.UsageError(
            "Nor `excel`, neither `mcnp` parameter is specified - nothing to do"
        )
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
    paths, path_info = create_path_info(materials_index, stp)
    materials_map = load_materials_map(materials) if materials else None
    used_materials_text = (
        get_used_materials(materials_map, path_info) if materials_map else None
    )
    if mcnp:
        _mcnp = Path(mcnp)
        joined_paths = join_paths(paths, separator)
        with select_output(override, output) as _output:
            merge_paths(_output, joined_paths, path_info, _mcnp, used_materials_text)
    if excel:
        start_cell_number = correct_start_cell_number(start_cell_number, mcnp)
        _excel = Path(excel)
        can_override(_excel, override)
        create_excel(_excel, paths, path_info, separator, start_cell_number)


def create_path_info(materials_index: str, stp: str):
    _materials_index = load_materials_index(materials_index)
    _stp = Path(stp)
    products, graph = parse_path(_stp)
    paths = create_bodies_paths(products, graph)
    path_info = extract_path_info(paths, _materials_index)
    return paths, path_info


def materials_spec_mapper(materials_map: Dict[int, str]):
    def _func(used_number: int):
        text = materials_map.get(used_number)
        if not text:
            text = f"m{used_number}  $ dummy: is to be replaced manually\n        1.001.31c  1.0"
        return text

    return _func


def get_used_materials(materials_map: Dict[int, str], path_info: pd.DataFrame):
    used_numbers = sorted(set(path_info["number"].values))
    used_materials_texts = list(map(materials_spec_mapper(materials_map), used_numbers))
    return "".join(used_materials_texts)


def join_paths(paths: List[List[str]], separator: str = "/") -> List[str]:
    return list(map(lambda path: separator.join(path), paths))


# TODO dvp: add logging


if __name__ == "__main__":
    mapstp()