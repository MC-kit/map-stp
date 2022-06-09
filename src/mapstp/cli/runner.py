"""Application to transfer meta information from STP.

For given STP file creates Excel table with a list
of STP paths to STP components, corresponding to cells
in MCNP model, would it be generated from the STP with SuperMC.

The Excel also contains material numbers, densities, correction factors,
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

from dataclasses import dataclass
from pathlib import Path

import click

from mapstp import __name__ as package_name
from mapstp import __summary__, __version__
from mapstp.cli.logging import init_logger, logger
from mapstp.excel import create_excel
from mapstp.materials import get_used_materials, load_materials_map
from mapstp.merge import join_paths, merge_paths
from mapstp.utils.io import can_override, find_first_cell_number, select_output
from mapstp.workflow import create_path_info


# TODO dvp: add customized configuring from a configuration toml-file.
@dataclass
class Config:
    override: bool = False


_USAGE = f"""
{__summary__}

For given STP file creates Excel table with a list
of STP paths to STP components, corresponding to cells
in MCNP model, would it be generated from the STP with SuperMC.

If MCNP file is also specified as the second `mcnp-file` argument,
then produces output MCNP file with STP paths inserted
as end of line comments after corresponding cells with prefix
"sep:". The material numbers and densities are set according
to the meta information provided in the STP.
"""


@click.command(help=_USAGE, name=package_name)
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
@click.version_option(__version__, prog_name=package_name)
@click.help_option()
@click.pass_context
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
    init_logger()
    logger.info("Running mapstp {}", __version__)
    cfg = ctx.ensure_object(Config)
    cfg.override = override
    paths, path_info = create_path_info(materials_index, stp)
    materials_map = load_materials_map(materials) if materials else None
    used_materials_text = (
        get_used_materials(materials_map, path_info) if materials_map else None
    )
    if mcnp:
        _mcnp = Path(mcnp)
        logger.info("Tagging model {}", mcnp)
        with select_output(override, output) as _output:
            joined_paths = join_paths(paths, separator)
            merge_paths(_output, joined_paths, path_info, _mcnp, used_materials_text)
    if excel:
        if not start_cell_number:
            start_cell_number = find_first_cell_number(mcnp) if mcnp else 1
        _excel = Path(excel)
        can_override(_excel, override)
        create_excel(_excel, paths, path_info, separator, start_cell_number)
        logger.info("Accompanying excel is saved to {}", _excel)
    logger.success("mapstp finished")


if __name__ == "__main__":
    mapstp()
