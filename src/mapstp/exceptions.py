"""Utility module to specify exception hierarchy for all tee package."""
import pandas as pd


class MyError(ValueError):
    """Base class for exceptions in the `mapstp` package."""


class FileError(MyError):
    """STP parser file format error."""


class ParseError(MyError):
    """STP parser syntax error."""


class PathInfoError(MyError):
    """Error on extracting information for labels specified in STP paths."""

    def __init__(self, msg: str, row: int, path_info: pd.DataFrame) -> None:
        """Create exception object with information on location in path_info caused the error.

        Args:
            msg: message
            row: row in path_info table
            path_info: the path_info table
        """
        MyError.__init__(
            self, msg + f" Row #{row}:\n" + f"{path_info.iloc[row].to_dict()}"
        )
