#!python
"""Clear environment from the old .dist-info packages.

This fixes https://github.com/python-poetry/poetry/issues/4526.
Should be fixed in poetry 1.2, but it's not available yet.
Run this if test_package() fails on pytest run.

"""
import platform
import shutil
import sys

from pathlib import Path


def get_packages_dir() -> Path:
    """Define packages location depending on system."""
    system = platform.system()
    if system == "Windows":
        site_packages = Path("Lib", "site-packages")
    else:
        python = f"python{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = Path("lib", python, "site-packages")
    result = Path(sys.prefix, site_packages)
    if not result.is_dir():
        raise ValueError(
            f"Cannot find site package for system {system} in folder {result}"
        )
    return result


def clear_mapstp_info_dists() -> None:
    """Remove all mapstp dist-info folders."""
    packages_dir = get_packages_dir()
    dists = list(packages_dir.glob("mapstp-*.dist-info"))
    for dist in dists:
        shutil.rmtree(dist)
    print("Run `poetry install` after running this script.")


if __name__ == "__main__":
    clear_mapstp_info_dists()
