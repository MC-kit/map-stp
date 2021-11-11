import re

from pathlib import Path

import pandas as pd
import pytest

from mapstp.cli.mapstp import VERSION, mapstp, meta
from mapstp.merge import CELL_START_PATTERN
from numpy.testing import assert_array_equal


def test_version_command(runner):
    result = runner.invoke(mapstp, args=["--version"], catch_exceptions=False)
    assert result.exit_code == 0, (
        "Should success on '--version' option: " + result.output
    )
    assert VERSION in result.output, "print version on 'version' command"


def test_help_command(runner):
    result = runner.invoke(mapstp, args=["--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: " in result.output
    expected = meta.__summary__.replace("\n", "")[:-40]
    actual = result.output.replace("\n", "")
    assert expected in actual


_COMMENT_PATTERN = re.compile(r"^\s{6}\$ stp: .*Body.*")


def extract_stp_comment_lines(lines):
    for line in lines:
        if _COMMENT_PATTERN.search(line):
            yield line


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
    df = pd.read_excel(excel, engine="openpyxl", sheet_name="Cells", index_col="cell")
    assert_array_equal(df.index.values, [100, 101, 102])


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


if __name__ == "__main__":
    pytest.main()
