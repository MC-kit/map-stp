from pathlib import Path


def can_override(path: Path, override: bool):
    if not override and path.exists():
        raise FileExistsError(
            f"File {path} already exists."
            "Consider to use '--override' command line option or remove the file."
        )
