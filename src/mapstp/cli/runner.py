"""Application to transfer meta information from STP.

For given STP file creates Excel table with a list
of STP paths to STP components, corresponding to cells
in MCNP model, would it be generated from the STP with SuperMC.

The Excel also contains material numbers, densities, correction factors,
and RWCL(RadWaste Check List) id. The values can be specified in the names of STP
components as special tags. A tag is denoted with bracket enclosed
specification at the end of component name: "Component name [<spec>]".
The spec may contain space separated entries:

    - m-<mnemonic> - first column in a special material-index.xlxs file.
    - f-<factor>   - float number for density correction factor
    - r-<rwcl>     - any label to categorize the components for RWCL

If MCNP file is also specified as the second `mcnp` argument,
then produces output MCNP file with STP paths inserted
as end of line comments after corresponding cells with prefix
"sep:". The material numbers and densities are set according
to the meta information provided in the STP.
"""

from __future__ import annotations

import sqlite3 as sq

from dataclasses import dataclass
from pathlib import Path

import click

from mapstp import __name__ as package_name
from mapstp import __summary__, __version__
from mapstp.cli.mapstp_logging import init_logger, logger
from mapstp.materials import get_used_materials_sql, load_materials_map
from mapstp.merge import merge_paths
from mapstp.save_table import create_excel
from mapstp.utils import can_override, select_output
from mapstp.workflow_sql import load_path_info, save_meta_info_from_paths


@dataclass
class Config:
    """Shared configuration."""

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
    "--sql",
    "-s",
    metavar="<sql-file>",
    type=click.Path(dir_okay=False),
    required=False,
    help="SQLite3 file with the model information",
)
@click.option(
    "--materials",
    metavar="<materials-file>",
    type=click.Path(dir_okay=False, exists=True),
    required=False,
    help="Text file containing MCNP materials specifications. "
    "If present, the selected materials present in this file are printed "
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
@click.argument(
    "mcnp",
    metavar="[mcnp-file]",
    type=click.Path(dir_okay=False, exists=True),
    required=True,
)
@click.version_option(__version__, prog_name=package_name)
@click.help_option()
@click.pass_context
def mapstp(  # noqa: PLR0913
    ctx: click.Context,
    output: str,
    excel: str,
    sql: str,
    materials: str | None,
    materials_index: str,
    mcnp: str,
    *,
    override: bool,
) -> None:
    """Transfers meta information from STP to MCNP model and Excel.

    Args:
        ctx: context object
        output: where to store resulting mcnp
        excel: excel to store mapping cell->tags, stp path, volume(if available)
        sql: as above but in SQLite3 table 'cell_info'
        materials: file with MCNP materials
        materials_index: excel with mnemonics mapping to materials and densities
        mcnp: input MCNP model - to be tagged in output
        override: override existing files if any, if false - raise exception
    """
    if not (mcnp or excel):
        msg = "Nor `excel`, neither `mcnp` parameter is specified - nothing to do"
        raise click.UsageError(msg)
    init_logger()
    logger.info("Running mapstp {}", __version__)
    cfg = ctx.ensure_object(Config)
    cfg.override = override
    con = sq.connect(sql)
    try:
        save_meta_info_from_paths(con, materials_index)
        if materials:
            materials_map = load_materials_map(materials)
            used_materials_text = get_used_materials_sql(con, materials_map)
        else:
            used_materials_text = None
        _mcnp = Path(mcnp)
        logger.info("Tagging model {}", mcnp)
        with select_output(output, override=override) as _output:
            path_info = load_path_info(con)
            merge_paths(_output, path_info, _mcnp, used_materials_text)
        _excel = Path(excel) if excel else Path(_mcnp.stem + "-cells.xlsx")
        can_override(_excel, override=override)
        create_excel(_excel, path_info)
        logger.info("Accompanying excel is saved to {}", _excel)
        logger.success("mapstp finished")
    finally:
        con.close()


if __name__ == "__main__":
    mapstp()
