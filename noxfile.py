"""Nox sessions.

See `Cjolowicz's article <https://cjolowicz.github.io/posts/hypermodern-python-03-linting>`_
"""
from typing import List

import platform
import shutil
import sys

from glob import glob
from pathlib import Path
from textwrap import dedent

import nox

# from nox.sessions import Session
try:
    from nox_poetry import Session, session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.

    Please install it using the following command:

    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None

# TODO dvp: uncomment when code and docs are more mature
nox.options.sessions = (
    "safety",
    "isort",
    "black",
    "lint",
    "mypy",
    # "xdoctest",  - TODO dvp: we don't use doctests so far
    "tests",
    # "codecov",
    # "docs",
)

package = "mapstp"
locations = f"src/{package}", "tests", "noxfile.py", "docs/source/conf.py"

supported_pythons = ["3.9", "3.8"]  # TODO dvp: add python 3.10
black_pythons = "3.9"
mypy_pythons = "3.9"
lint_pythons = "3.9"

on_windows = platform.system() == "Windows"


# @contextmanager
# def collect_dev_requirements(session: Session) -> Generator[str, None, None]:
#     """Create file with development requirements.
#
#     Remove the file on exit.
#
#     Yields:
#         Temporary file name.
#     """
#     req_path = os.path.join(tempfile.gettempdir(), os.urandom(24).hex())
#     try:
#         session.run(
#             "poetry",
#             "export",
#             "--dev",
#             "--without-hashes",
#             "--format=requirements.txt",
#             f"--output={req_path}",
#             external=True,
#         )
#         yield req_path
#     finally:
#         os.unlink(req_path)


# # see https://stackoverflow.com/questions/59768651/how-to-use-nox-with-poetry
# def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
#     """Install packages constrained by Poetry's lock file.
#
#     This function is a wrapper for nox.sessions.Session.install. It
#     invokes pip to install packages inside of the session's virtualenv.
#     Additionally, pip is passed a constraints file generated from
#     Poetry's lock file, to ensure that the packages are pinned to the
#     versions specified in poetry.lock. This allows you to manage the
#     packages as Poetry development dependencies.
#
#     Arguments:
#         session: The Session object.
#         args: Command-line arguments for pip.
#         kwargs: Additional keyword arguments for Session.install.
#     """
#     with collect_dev_requirements(session) as req_path:
#         session.install(f"--constraint={req_path}", *args, **kwargs)


@session(python="3.9")
def safety(s: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = s.poetry.export_requirements()
    s.install("safety")
    s.run("safety", "check", "--full-report", f"--file={requirements}")


# @nox.session(python=supported_pythons, venv_backend="venv")
@session(python=supported_pythons)
def tests(s: Session) -> None:
    """Run the test suite."""
    # args = session.posargs or ["--cov"]
    # session.run(
    #     "poetry",
    #     "install",
    #     "--no-dev",
    #     external=True,
    # )
    # install_with_constraints(session, "pytest", "pytest-mock")
    # if "--cov" in args:
    #     install_with_constraints(session, "pytest-cov", "coverage[toml]")
    # session.run("pytest", *args)
    # if "--cov" in args:
    #     session.run("coverage", "report", "--show-missing", "--skip-covered")
    #     session.run("coverage", "html")
    s.install(".")
    s.install("coverage[toml]", "pytest", "pygments")
    try:
        s.run("coverage", "run", "--parallel", "-m", "pytest", *s.posargs)
    finally:
        if s.interactive:
            s.notify("coverage", posargs=[])


@session
def coverage(s: Session) -> None:
    """Produce the coverage report.

    To obtain html report run
        nox -rs coverage -- html
    """
    args = s.posargs or ["report"]

    s.install("coverage[toml]")

    if not s.posargs and any(Path().glob(".coverage.*")):
        s.run("coverage", "combine")

    s.run("coverage", *args)

    # if "html" not in args:
    #     session.run("coverage", "html")


@session(python=supported_pythons)
def typeguard(s: Session) -> None:
    """Runtime type checking using Typeguard."""
    s.install(".")
    s.install("pytest", "typeguard", "pygments")
    s.run("pytest", f"--typeguard-packages={package}", *s.posargs)


@session(python="3.9")
def isort(s: Session) -> None:
    """Organize imports."""
    s.install("isort")
    search_patterns = [
        "*.py",
        "mapstp/*.py",
        "tests/*.py",
        "benchmarks/*.py",
        "profiles/*.py",
        #        "adhoc/*.py",
    ]
    files_to_process: List[str] = sum(
        map(lambda p: glob(p, recursive=True), search_patterns), []
    )
    s.run(
        "isort",
        "--check",
        "--diff",
        *files_to_process,
        external=True,
    )


@session(python=black_pythons)
def black(s: Session) -> None:
    """Run black code formatter."""
    args = s.posargs or locations
    s.install("black")
    s.run("black", *args)


@session(python=lint_pythons)
def lint(s: Session) -> None:
    """Lint using flake8."""
    args = s.posargs or locations
    s.install(
        "flake8",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "flake8-import-order",
        "darglint",
    )
    s.run("flake8", *args)


@session(python=mypy_pythons)
def mypy(s: Session) -> None:
    """Type-check using mypy."""
    args = s.posargs or [
        "src/mapstp",
        "docs/source/conf.py",
    ]  # TODO dvp: add other locations
    s.install("mypy", "types-setuptools")
    s.run("mypy", *args)


@session(python=supported_pythons)
def xdoctest(s: Session) -> None:
    """Run examples with xdoctest."""
    args = s.posargs or ["all"]
    s.install(".")
    s.install("xdoctest[colors]")
    s.run("python", "-m", "xdoctest", package, *args)


@session(name="docs-build", python="3.10")
def docs_build(s: Session) -> None:
    """Build the documentation."""
    args = s.posargs or ["docs/source", "docs/_build"]
    s.install(".")
    s.install(
        "sphinx",
        "sphinx-click",
        "sphinx-rtd-theme",
        # "sphinxcontrib-htmlhelp",
        # "sphinxcontrib-jsmath",
        "sphinxcontrib-napoleon",
        # "sphinxcontrib-qthelp",
        "sphinx-autodoc-typehints",
        # "sphinx_autorun",
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    s.run("sphinx-build", *args)


@session(python="3.10")
def docs(s: Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = s.posargs or ["--open-browser", "docs/source", "docs/_build"]
    s.install(".")
    s.install(
        "sphinx",
        "sphinx-autobuild",
        "sphinx-click",
        "sphinx-rtd-theme",
        # "sphinxcontrib-htmlhelp",
        # "sphinxcontrib-jsmath",
        # "sphinxcontrib-napoleon",
        # "sphinxcontrib-qthelp",
        # "sphinx-autodoc-typehints",
        # "sphinx_autorun",
    )

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    s.run("sphinx-autobuild", *args)


# @nox.session(python="3.9")
# def docs(session: Session) -> None:
#     """Build the documentation."""
#     session.run("poetry", "install", "--no-dev", external=True)
#     install_with_constraints(
#         session,
#         "sphinx",
#         "sphinx-autobuild",
#         "sphinxcontrib-htmlhelp",
#         "sphinxcontrib-jsmath",
#         "sphinxcontrib-napoleon",
#         "sphinxcontrib-qthelp",
#         "sphinx-autodoc-typehints",
#         "sphinx_autorun",
#         "sphinx-rtd-theme",
#     )
#     if session.interactive:
#         session.run(
#             "sphinx-autobuild",
#             "--port=0",
#             "--open-browser",
#             "docs/source",
#             "docs/_build/html",
#         )
#     else:
#         session.run("sphinx-build", "docs/source", "docs/_build")


@session(python="3.9")
def codecov(s: Session) -> None:
    """Upload coverage data."""
    s.run("poetry", "install", "--no-dev", external=True)
    s.install(
        "coverage[toml]",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "codecov",
    )
    s.run("coverage", "xml", "--fail-under=0")
    s.run("codecov", *s.posargs)


# @session(python="3.9", venv_backend="venv")
# def test_nox(s: Session) -> None:
#     """Debug nox itself with this session."""
#     path = Path(s.bin)
#     print("bin", path.parent)
#     s.run("pip", "install", ".")
