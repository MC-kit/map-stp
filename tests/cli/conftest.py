from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contextlib import contextmanager
from pathlib import Path

import pytest

from eliot import FileDestination, add_destinations, remove_destination
from rich.console import Console

from tests.cli._memory_destination import MemoryDestination

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from contextlib import _GeneratorContextManager

    from cyclopts import App


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
