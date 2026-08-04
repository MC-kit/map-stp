from __future__ import annotations

from typing import TYPE_CHECKING

import re
import shutil

from pathlib import Path

import pytest

from cyclopts import MissingArgumentError

from mapstp import __summary__
from mapstp.__main__ import app as mapstp
from mapstp.materials import load_materials_map
from mapstp.utils._io import find_first_cell_number, read_mcnp_sections
from mapstp.utils._re import MATERIAL_PATTERN, VOID_CELL_START_PATTERN

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable

    from tests.cli._memory_destination import MemoryDestination
    from tests.cli._types import Runner


def test_tag_help_command(cyclopts_runner: Runner) -> None:
    out = cyclopts_runner(mapstp, ["tag", "--help"])
    assert "Transfers meta" in out
    expected = __summary__.replace("\n", "")[:-40]
    actual = out.replace("\n", "")
    assert expected in actual


_COMMENT_PATTERN = re.compile(r"^\s{6}\$ stp: .*")


def extract_stp_comment_lines(lines: Iterable[str]) -> Generator[str]:
    for line in lines:
        if _COMMENT_PATTERN.search(line):
            yield line


def _extract_material_first_lines(lines: Iterable[str]) -> Generator[tuple[int, str]]:
    for line in lines:
        match = MATERIAL_PATTERN.search(line)
        if match:
            yield int(match["material"]), line


def extract_first_void_cell_lines(lines: Iterable[str]) -> Generator[str]:
    for line in lines:
        if VOID_CELL_START_PATTERN.search(line):
            yield line


def test_commenting_with_sql(cyclopts_runner: Runner, data: Path) -> None:
    output = Path("test1-with-comments.i")
    mcnp = data / "test1.i"
    original_sql = data / "test1.sqlite"
    cd_tmpdir = Path.cwd()
    sql = cd_tmpdir / "test1.sqlite"
    shutil.copy(original_sql, sql)
    cyclopts_runner(
        mapstp,
        ["tag", "--output", str(output), "--sql", str(sql), str(mcnp)],
        exit_on_error=False,
    )
    assert output.exists(), f"Should create output file {output}"
    sections = read_mcnp_sections(output)
    assert sections.remainder is None
    with output.open() as stream:
        lines = list(extract_stp_comment_lines(stream.readlines()))
    assert len(lines) == 3


def test_commenting_with_sql_to_stdout(cyclopts_runner: Runner, data: Path) -> None:
    mcnp = data / "test1.i"
    cyclopts_runner(
        mapstp,
        ["tag", "--sql", str(mcnp.with_suffix(".sqlite")), str(mcnp)],
        exit_on_error=False,
    )
    assert Path("test1-tagged.i").exists(), "Should create test1-tagged.i"


def test_structured_logging_of_materials_path(
    cyclopts_runner: Runner,
    eliot_mem_trace: MemoryDestination,
    data: Path,
) -> None:
    mcnp = data / "test1.i"
    sql = data / "test1.sqlite"
    materials = data / "materials-1.txt"
    cyclopts_runner(
        mapstp,
        ["tag", "--sql", str(sql), "--materials", str(materials), str(mcnp)],
        exit_on_error=False,
    )
    assert any(m.get("materials") == materials.absolute() for m in eliot_mem_trace.messages), (
        "Should log provided materials path as structured Eliot metadata"
    )


def test_success_fields_when_output_not_specified(
    cyclopts_runner: Runner,
    eliot_mem_trace: MemoryDestination,
    data: Path,
) -> None:
    """Test line 175: if output is not sys.stdout branch when output not specified."""
    mcnp = data / "test1.i"
    sql = data / "test1.sqlite"
    cyclopts_runner(
        mapstp,
        ["tag", "--sql", str(sql), str(mcnp)],
        exit_on_error=False,
    )
    # When output is not specified, it defaults to a file (not sys.stdout)
    # so the success event should include the output field
    success_messages = [
        m
        for m in eliot_mem_trace.messages
        if m.get("action_status") == "succeeded" and m.get("action_type") == "tag mcnp"
    ]
    assert success_messages, "Should have at least one success message"
    success_msg = success_messages[0]
    assert "output" in success_msg, (
        "When output is not specified, default output file should be logged in success_fields"
    )
    assert success_msg["output"] == Path("test1-tagged.i")


def test_info_assignment_with_sql(cyclopts_runner: Runner, data: Path) -> None:
    output = Path("test-extract-info-prepared.i")
    excel = Path("test-extract-info.xlsx")
    original_sql = data / "test-extract-info.sqlite"
    sql = original_sql.name
    shutil.copy(original_sql, sql)
    mcnp = data / "test-extract-info.i"
    # uses internal default material index
    cyclopts_runner(
        mapstp,
        [
            "tag",
            "--output",
            str(output),
            "--excel",
            str(excel),
            "--sql",
            str(sql),
            "--mcnp-encoding",
            "cp1251",
            str(mcnp),
        ],
        exit_on_error=False,
    )
    assert output.exists(), f"Should create output file {output}"
    with output.open(encoding="cp1251") as stream:
        lines = list(stream.readlines())
    assert "           ( -2005 2010 2006 -2017 -2009 2018)\n" in lines, (
        "The specification should be wrapped after material insertion to the first line"
    )
    stp_comment_lines = list(extract_stp_comment_lines(lines))
    assert len(stp_comment_lines) == 5
    assert "Inconel718" in stp_comment_lines[3]
    first_void_lines = list(extract_first_void_cell_lines(lines))
    assert len(first_void_lines) == 6


@pytest.mark.parametrize(
    "mcnp,expected",
    [
        ("test-extract-info.i", 2000),
    ],
)
def test_correct_start_cell_number(data: Path, mcnp: str | Path, expected: int) -> None:
    if mcnp:
        mcnp = data / mcnp
    actual = find_first_cell_number(mcnp)
    assert actual == expected


def test_run_tag_without_args(
    cyclopts_runner: Callable,
    eliot_file_trace: Callable,
) -> None:
    with eliot_file_trace("test.log"), pytest.raises(MissingArgumentError, match="mcnp"):
        assert "Missing argument" in cyclopts_runner(
            mapstp,
            ["tag"],
            exit_on_error=False,
        )


def select_cell_and_stp_lines(lines: Iterable[str]) -> dict[int, str]:
    selected = list(filter(lambda x: re.search(r"^\s{0,5}\d+\s+\d", x) or "$ stp: " in x, lines))
    res = {}
    for i, line in enumerate(selected):
        if "$ stp: " in line:
            cell = int(selected[i - 1].split(maxsplit=2)[0])
            res[cell] = line
    return res


def check_materials(materials: Path, number_of_materials: int) -> None:
    materials_dict = load_materials_map(materials)
    assert len(materials_dict) == number_of_materials, f"There should be {number_of_materials} materials in {materials}"
    for i in range(1, 4):
        assert i in materials_dict
    material_1_first_row = materials_dict[1].split("\n")[1].strip()
    assert material_1_first_row.startswith("5010.31d")


if __name__ == "__main__":
    pytest.main()
