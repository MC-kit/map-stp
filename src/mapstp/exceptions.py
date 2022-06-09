"""Utility module to specify exception hierarchy for all tee package."""
import pandas as pd


class MyError(ValueError):
    """Base class for exceptions in the `mapstp` package."""


class FileError(MyError):
    """STP parser file format error."""


class STPParserError(MyError):
    """STP parser syntax error."""

    def __init__(self, message: str = "The STP is invalid") -> None:
        """Create STP parsing specific exception.

        Args:
            message: explanation, what happened
        """
        super().__init__(self, message)


class PathInfoError(MyError):
    """Error on extracting information for labels specified in STP paths."""

    def __init__(self, message: str, row: int, path_info: pd.DataFrame) -> None:
        """Create exception object with information on location in path_info caused the error.

        Args:
            message:  explanation, what happened
            row: row in path_info table
            path_info: the path_info table
        """
        MyError.__init__(
            self, message + f" Row #{row}:\n" + f"{path_info.iloc[row].to_dict()}"
        )
