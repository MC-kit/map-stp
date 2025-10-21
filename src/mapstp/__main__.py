"""CLI mapstp interface."""

from __future__ import annotations

from typing import Annotated, Final, cast

import logging
import sqlite3 as sq
import sys

from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

import cyclopts

from cyclopts import App, Parameter, types  # noqa: TC002 - types are used in run time
from eliot import start_task
from rich.console import Console

from mapstp import __summary__, __version__
from mapstp.cli import summary2sqlite as do_summary2sqlite
from mapstp.csv2sqlite import csv2sqlite as do_csv2sqlite
from mapstp.mapstp_logging import NAME, PREFIX, init_logging
from mapstp.materials import get_used_materials_sql, load_materials_map
from mapstp.merge import merge_paths
from mapstp.save_meta_info import load_path_info, save_meta_info_from_paths
from mapstp.save_table import create_excel
from mapstp.utils import can_override

DEFAULT_CONFIG_PATH: Final[Path] = PREFIX.with_suffix(".toml")
DEFAULT_ELIOT_LOG_PATH: Final[Path] = PREFIX.with_suffix(".log")

_TAG_USAGE: Final[str] = f"""
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


console = Console()
app = App(
    name=NAME,  # ty: ignore[unknown-argument]
    version=__version__,
    console=console,
    help=__summary__,  # ty: ignore[unknown-argument]
    help_format="restructuredtext",
)

_LOG = logging.getLogger("mapstp.main")


@Parameter(name="*")  # https://cyclopts.readthedocs.io/en/latest/cookbook/sharing_parameters.html
@dataclass
class Common:
    """Common for all commands command line options."""

    override: bool = False
    "Override existing output files [default: no]"

    mcnp_encoding: str = "utf8"
    """Encoding of the MCNP file, if generated with GEOUNED - `utf8`, if with SuperMC - `cp1251`"""


@app.command
def tag(  # noqa: PLR0913
    mcnp: types.ResolvedExistingFile,
    sql: Annotated[
        types.ResolvedExistingFile,
        Parameter(
            name=["--sql", "-s"],
        ),
    ],
    *,
    output: Annotated[
        types.ResolvedFile | None,
        Parameter(
            name=["--output", "-o"],
        ),
    ] = None,
    materials_index: Annotated[
        types.ResolvedExistingFile | None,
        Parameter(
            name=["--materials-index", "-m"],
            help=(
                "Excel file containing materials mnemonics and materials for an MCNP model "
                "(default: file from the package internal data corresponding to ITER C-model)"
            ),
        ),
    ] = None,
    materials: Annotated[
        types.ResolvedExistingFile | None,
        Parameter(
            name="--materials",
            help="Text file containing MCNP materials specifications. "
            "If present, the selected materials present in this file are printed "
            "to the `output` MCNP model, so, it becomes complete valid model",
        ),
    ] = None,
    excel: Annotated[
        types.ResolvedFile | None,
        Parameter(
            name=["--excel", "-e"],
        ),
    ] = None,
    mcnp_encoding: str = "utf8",
    geouned_format: bool = False,
    common: Common | None = None,
) -> None:
    """Transfers meta information from STP to MCNP model and Excel.

    Parameters
    ----------
    output
        File to write the MCNP with marked cells (default: computed),
    excel
        excel to store mapping cell->tags, stp path, volume
    sql
        SQLite3 file with the model information,
    materials
        file with MCNP materials
    materials_index
        excel with mnemonics mapping to materials and densities
    mcnp
        input MCNP model - to be tagged in output
    mcnp_encoding
        ... of the MCNP file, if generated with GEOUNED - ``utf8``, if with SuperMC - ``cp1251``
    geouned_format:
        the MCNP file is produced by GeoUNED, where volume and STEP paths are already
        specified, don't change, just check
    """
    if common is None:  # pragma: no cover
        common = Common()
    with (
        start_task(action_type="tag mcnp", mcnp=mcnp, sql=sql) as logger,
        closing(sq.connect(sql)) as con,
    ):
        save_meta_info_from_paths(con, materials_index)
        if materials:
            materials_map = load_materials_map(materials)
            used_materials_text: str | None = get_used_materials_sql(con, materials_map)
        else:
            used_materials_text = None
        _LOG.info("mapstp %s", __version__)
        _LOG.info("Tagging model %s", mcnp)
        if output is None:
            output = Path(mcnp.stem + "-tagged").with_suffix(mcnp.suffix)
        can_override(output, override=common.override)
        with output.open(mode="w", encoding="utf8") as _output:
            path_info = load_path_info(con)
            merge_paths(
                _output,
                path_info,
                mcnp,
                used_materials_text,
                geouned_format=geouned_format,
                encoding=mcnp_encoding,
            )
        if excel is None:
            excel = Path(mcnp.stem + "-cells.xlsx")
        can_override(excel, override=common.override)
        create_excel(excel, path_info)
        logger.add_success_fields(excel=excel)
        if output is not sys.stdout:
            logger.add_success_fields(output=output)


@app.command
def csv2sqlite(
    csv: types.ExistingCsvPath,
    sql: Annotated[
        types.NonExistentFile,
        Parameter(
            name=["--sql", "-s"],
        ),
    ],
    common: Common | None = None,
) -> None:
    """Convert CSV with metainfo from SpaceClaim model to sqlite.

    Parameters
    ----------
    csv
        CSV path
    sql
        Path to Sqlite database to store ``cells`` table.
    """
    if common is None:  # pragma: no cover
        common = Common()
    do_csv2sqlite(csv, sql, override=common.override)


@app.command
def summary2sqlite(
    summary: types.ExistingPath,
    sql: Annotated[
        types.NonExistentFile,
        Parameter(
            name=["--sql", "-s"],
        ),
    ],
    common: Common | None = None,
) -> None:
    """Convert GeoUNED summary file to sqlite.

    Parameters
    ----------
    summary
        path to summary.txt file
    sql
        Path to Sqlite database to store ``cells`` table.
    """
    if common is None:  # pragma: no cover
        common = Common()
    do_summary2sqlite(summary, sql, override=common.override)


@app.meta.default
def meta(
    *tokens: Annotated[str, Parameter(show=False, allow_leading_hyphen=True)],  # ty: ignore[unknown-argument]
    config: types.TomlPath = DEFAULT_CONFIG_PATH,
    eliot_log: Path = DEFAULT_ELIOT_LOG_PATH,
) -> None:
    """Transfer meta information from STP to MCNP.

    Parameters
    ----------
    config, optional
        configuration file, by default mapstp.toml
    eliot_log, optional
        file for structured eliot logging, by default mapstp.log
    """
    toml_cfg = cyclopts.config.Toml(
        config,
        root_keys=["tool", "mapstp"],
        search_parents=True,
    )
    env_cfg = cyclopts.config.Env(prefix=NAME)
    app.config = cast("tuple[str, ...]", (toml_cfg, env_cfg))
    _console = app.console
    init_logging(_console, eliot_log)
    with start_task(action_type=NAME, version=__version__, working_dir=Path.cwd().absolute()):
        _console.print(NAME, __version__, style="bold dark_olive_green3")
        _console.print("eliot log: ", eliot_log.absolute(), style="dim")
        if "pytest" in sys.modules:
            app(tokens, result_action="return_value")
        else:
            app(tokens)
        _console.rule("✨ Done :smiley:", style="bold yellow1")


def main() -> None:  # pragma: no cover
    """Run mapstp application."""
    app.meta()


if __name__ == "__main__":
    main()
