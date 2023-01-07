from typing import Dict, Iterable

import re

from pathlib import Path

import pandas as pd
import pytest

from mapstp.cli.runner import __summary__, __version__, mapstp
from mapstp.materials import load_materials_map
from mapstp.utils.io import find_first_cell_number, read_mcnp_sections
from mapstp.utils.re import CELL_START_PATTERN, MATERIAL_PATTERN
from numpy.testing import assert_array_equal


# noinspection PyTypeChecker
def test_version_command(runner):
    result = runner.invoke(mapstp, args=["--version"], catch_exceptions=False)
    assert result.exit_code == 0, (
        "Should success on '--version' option: " + result.output
    )
    assert __version__ in result.output, "print version on 'version' command"


# noinspection PyTypeChecker
def test_help_command(runner):
    result = runner.invoke(mapstp, args=["--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: " in result.output
    expected = __summary__.replace("\n", "")[:-40]
    actual = result.output.replace("\n", "")
    assert expected in actual


_COMMENT_PATTERN = re.compile(r"^\s{6}\$ stp: .*Body.*")


def extract_stp_comment_lines(lines):
    for line in lines:
        if _COMMENT_PATTERN.search(line):
            yield line


def _extract_material_first_lines(lines):
    for line in lines:
        match = MATERIAL_PATTERN.search(line)
        if match:
            yield int(match["material"]), line


def test_commenting1(runner, tmp_path, data):
    output: Path = tmp_path / "test1-with-comments.i"
    stp = data / "test1.stp"
    mcnp = data / "test1.i"
    result = runner.invoke(
        mapstp,
        args=["--output", str(output), str(stp), str(mcnp)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert output.exists(), f"Should create output file {output}"
    sections = read_mcnp_sections(output)
    assert sections.remainder is None
    with output.open() as stream:
        lines = list(extract_stp_comment_lines(stream.readlines()))
    assert len(lines) == 3


def test_commenting1_to_stdout(runner, tmp_path, data):
    stp = data / "test1.stp"
    mcnp = data / "test1.i"
    result = runner.invoke(
        mapstp,
        args=[str(stp), str(mcnp)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert "Body1" in result.output


def test_commenting1_with_excel(runner, tmp_path, data):
    output: Path = tmp_path / "test1-with-comments.i"
    excel: Path = tmp_path / "test1.xlsx"
    stp = data / "test1.stp"
    mcnp = data / "test1.i"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            str(excel),
            "--start-cell-number",
            str(100),
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert excel.exists(), f"Should create Excel file {excel}"
    path_info_df = pd.read_excel(
        excel, engine="openpyxl", sheet_name="Cells", index_col="cell"
    )
    assert_array_equal(path_info_df.index.to_numpy(), [100, 101, 102])


@pytest.mark.parametrize(
    "touch_output, touch_excel, expected",
    [
        (False, False, 0),
        (True, False, 1),
        (False, True, 1),
        (True, True, 1),
    ],
)
def test_override(runner, tmp_path, data, touch_output, touch_excel, expected):
    output: Path = tmp_path / "test1-with-comments.i"
    excel: Path = tmp_path / "test1.xlsx"
    if touch_output:
        output.touch()
        assert output.exists()
    if touch_excel:
        excel.touch()
        assert excel.exists()
    stp = data / "test1.stp"
    mcnp = data / "test1.i"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            str(excel),
            "--start-cell-number",
            str(100),
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=True,
    )
    assert result.exit_code == expected, result.output


def extract_first_void_cell_lines(lines):
    for line in lines:
        if CELL_START_PATTERN.search(line):
            yield line


def test_info_assignment(runner, tmp_path, data):
    output: Path = tmp_path / "test-extract-info-prepared.i"
    excel: Path = tmp_path / "test-extract-info.xlsx"
    stp = data / "test-extract-info.stp"
    mcnp = data / "test-extract-info.i"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            excel,
            "--start-cell-number",
            "2000",
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert output.exists(), f"Should create output file {output}"
    with output.open(encoding="cp1251") as stream:
        lines = list(stream.readlines())
    stp_comment_lines = list(extract_stp_comment_lines(lines))
    assert len(stp_comment_lines) == 5
    assert "Inconel718" in stp_comment_lines[3]
    first_void_lines = list(extract_first_void_cell_lines(lines))
    assert len(first_void_lines) == 2


@pytest.mark.parametrize(
    "mcnp, expected",
    [
        ("test-extract-info.i", 2000),
    ],
)
def test_correct_start_cell_number(data, mcnp, expected):
    if mcnp:
        mcnp = data / mcnp
    actual = find_first_cell_number(mcnp)
    assert actual == expected


def test_cli_correct_start_cell_number(runner, tmp_path, data):
    output: Path = tmp_path / "test-extract-info-prepared.i"
    excel: Path = tmp_path / "test-extract-info.xlsx"
    stp = data / "test-extract-info.stp"
    mcnp = data / "test-extract-info.i"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            excel,
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert output.exists(), f"Should create output file {output}"
    actual = find_first_cell_number(output)
    assert actual == 2005, "The first void cell number is wrong"


def test_run_without_args(runner):
    result = runner.invoke(
        mapstp,
        args=[],
        catch_exceptions=False,
    )
    assert result.exit_code == 2, result.output
    assert "Missing argument" in result.output


def test_run_without_args_for_output(runner, data):
    stp = data / "test-extract-info.stp"
    result = runner.invoke(
        mapstp,
        args=[str(stp)],
        catch_exceptions=False,
    )
    assert result.exit_code == 2, result.output
    assert "Nor `excel`, neither `mcnp` parameter is specified" in result.output


def test_run_without_excel_output_only(runner, tmp_path, data):
    stp = data / "test-extract-info.stp"
    excel: Path = tmp_path / "test-extract-info.xlsx"
    result = runner.invoke(
        mapstp,
        args=["--excel", excel, str(stp)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert excel.exists(), f"Excel file {excel} is not created"


def select_cell_and_stp_lines(lines: Iterable[str]) -> Dict[int, str]:
    selected = list(
        filter(lambda x: re.search(r"^\s{0,5}\d+\s+\d", x) or "$ stp: " in x, lines)
    )
    res = {}
    for i, line in enumerate(selected):
        if "$ stp: " in line:
            cell = int(selected[i - 1].split(maxsplit=2)[0])
            res[cell] = line
    return res


def test_export_materials(runner, tmp_path, data):
    output: Path = tmp_path / "test-extract-info-prepared.i"
    excel: Path = tmp_path / "test-extract-info.xlsx"
    stp = data / "test-extract-info.stp"
    mcnp = data / "test-extract-info.i"
    materials = data / "111.txt"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            excel,
            "--materials",
            str(materials),
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert output.exists(), f"Should create output file {output}"
    sections = read_mcnp_sections(output)
    cell2stp = select_cell_and_stp_lines(sections.cells.split("\n"))
    assert 2004 in cell2stp
    assert sections.cards, f"Control cards should be presented in {output}"
    lines = sections.cards.split("\n")
    material_lines = dict(_extract_material_first_lines(lines))
    assert len(material_lines) == 2, f"There should be two materials in {output}"
    assert (
        material_lines[111]
        == "m111    24050.31c   6.88386e-004 $CR 50 WEIGHT(%) 17.2500 AB(%)  4.34"
    )


def test_tnes(runner, tmp_path, data):
    """STP without components."""
    output: Path = tmp_path / "test-tnes.i"
    excel: Path = tmp_path / "test-tnes.xlsx"
    stp = data / "tnes.stp"
    mcnp = data / "tnes.i"
    material_index = data / "tnes-mi-22-12-19.xlsx"
    materials = data / "tnes-materials.txt"
    result = runner.invoke(
        mapstp,
        args=[
            "--output",
            str(output),
            "--excel",
            excel,
            "--materials-index",
            str(material_index),
            "--materials",
            str(materials),
            str(stp),
            str(mcnp),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    assert output.exists(), f"Should create output file {output}"
    sections = read_mcnp_sections(output)
    cell2stp = select_cell_and_stp_lines(sections.cells.split("\n"))
    assert 1 in cell2stp
    assert sections.cards, f"Control cards should be presented in {output}"
    check_materials(materials, 3)
    check_materials(output, 4)
    path_info_df = pd.read_excel(excel, index_col="cell")
    path = path_info_df.loc[1]["STP path"]
    assert "[m-reflector]" in path


def check_materials(materials, number_of_materials):
    materials_dict = load_materials_map(materials)
    assert (
        len(materials_dict) == number_of_materials
    ), f"There should be {number_of_materials} materials in {materials}"
    for i in range(1, 4):
        assert i in materials_dict
    material_1_first_row = materials_dict[1].split("\n")[1].strip()
    assert material_1_first_row.startswith("5010.31d")


if __name__ == "__main__":
    pytest.main()
