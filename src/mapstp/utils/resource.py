"""Utility methods to access a package data."""

from typing import Callable, cast

import inspect

from pathlib import Path

import pkg_resources as pkg


def filename_resolver(package: str = None) -> Callable[[str], str]:
    """Create method to find data file name.

    Uses resource manager to handle all the cases of the deployment.

    Args:
        package: the package below which the data is stored.
                 Optional, if not specified, the package of caller will be used.

    Returns:
        callable which appends the argument to the package folder.
    """
    package = _resolve_package(package)
    resource_manager = pkg.ResourceManager()  # type: ignore

    def func(resource: str) -> str:
        return cast(str, resource_manager.resource_filename(package, resource))

    func.__doc__ = f"Computes file names for resources located in {package}"

    return func


def path_resolver(package: str = None) -> Callable[[str], Path]:
    """Create method to find data path.

    Uses :meth:`file_resolver`.

    Args:
        package: the package below which the data is stored.
                 Optional, if not specified, the package of caller will be used.

    Returns:
        callable which appends the argument to the package folder adt returns as Path.
    """
    # Note: we should define package here to have proper offset in callers stack.
    package = _resolve_package(package)
    resolver = filename_resolver(package)

    def func(resource: str) -> Path:
        filename = resolver(resource)
        return Path(filename)

    func.__doc__ = f"Computes Path for resources located in {package}"

    return func


def _resolve_package(package: str = None) -> str:
    if package is None:
        module = inspect.getmodule(inspect.stack()[2][0])
        if module is None:
            raise ValueError("Cannot define package.")  # pragma: no cover
        package = module.__name__
    return package
