from __future__ import annotations

from typing import TYPE_CHECKING

from pathlib import Path

from mapstp import __summary__, __version__
from mapstp.__main__ import app as mapstp
from mapstp.__main__ import meta

if TYPE_CHECKING:
    from tests.cli._types import Runner


def test_version(cyclopts_runner: Runner) -> None:
    out = cyclopts_runner(mapstp, ["--version"])
    assert __version__ in out


def test_help_command(cyclopts_runner: Runner) -> None:
    out = cyclopts_runner(mapstp, ["--help"])
    assert "Usage: " in out
    expected = __summary__.replace("\n", "")[:-40]
    actual = out.replace("\n", "")
    assert expected in actual


def test_meta():
    meta("--help")


def test_meta_with_command():
    meta("tag", "--help")


def test_meta_with_args(data, cd_tmpdir):  # noqa: ARG001
    mcnp = data / "test1.i"
    meta("tag", "--sql", str(mcnp.with_suffix(".sqlite")), str(mcnp))
    assert Path("test1-tagged.i").exists(), "Should create test1-tagged.i"
