from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contextlib import contextmanager
from pathlib import Path

import pytest

from eliot import FileDestination, MemoryLogger, add_destinations, remove_destination
from rich.console import Console

from mapstp.materials_index import load_materials_index

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from contextlib import _GeneratorContextManager

    import pandas as pd

    from cyclopts import App


_DATA = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def data() -> Path:
    """Compute the path to test data.

    Returns
    -------
    Path: to test data (absolute).
    """
    return _DATA.absolute()


@pytest.fixture(scope="session")
def materials() -> pd.DataFrame:
    """Materials dataframe."""
    return load_materials_index()


@pytest.fixture
def cd_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporarily change to temp directory.

    Returns
    -------
    Path: to temporary directory
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def eliot_file_trace() -> Callable[[Path | str], _GeneratorContextManager[None]]:
    """Eliot trace to file."""

    @contextmanager
    def _wrap(path: Path | str) -> Generator[None]:
        if isinstance(path, str):
            path = Path(path)
        with path.open("w") as fid:
            pth = FileDestination(fid)
            add_destinations(pth)
            try:
                yield
            finally:
                remove_destination(pth)

    return _wrap


class MemoryDestination(MemoryLogger):  # type: ignore[misc]
    """Eliot memory logger."""

    def __call__(self, message: dict[str, Any]) -> None:
        self.write(message)

    def check_message(self, key: str, msg: str) -> bool:
        """Check message in memory log."""
        return any(key in m and msg in m[key] for m in self.messages)


@pytest.fixture
def eliot_mem_trace() -> Generator[MemoryDestination]:
    """Eliot trace to memory logger."""
    mem = MemoryDestination()
    add_destinations(mem)
    try:
        yield mem
    finally:
        remove_destination(mem)


@pytest.fixture
def cyclopts_runner(
    cd_tmpdir: Path,  # noqa: ARG001
) -> Callable[..., str]:
    """Run cyclopts application in temporary directory and isolated console.

    Parameters
    ----------
    cd_tmpdir
        Reuse fixture cd_tmpdir

    Returns
    -------
        Callable to run the application returning the command output.
    """

    def _wrapper(
        app: App,
        args: None | str | Iterable[str] = None,
        **kwargs: Any,
    ) -> str:
        console = Console()
        with console.capture() as capture:
            app(args, console=console, result_action="return_value", **kwargs)
        return capture.get()

    return _wrapper
