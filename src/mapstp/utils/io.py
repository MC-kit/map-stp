from pathlib import Path

from mapstp.utils.re import CELL_START_PATTERN


def can_override(path: Path, override: bool):
    if not override and path.exists():
        raise FileExistsError(
            f"File {path} already exists."
            "Consider to use '--override' command line option or remove the file."
        )


def find_first_cell_number(mcnp):
    _mcnp = Path(mcnp)
    with _mcnp.open(encoding="cp1251") as stream:
        for line in stream:
            match = CELL_START_PATTERN.search(line)
            if match:
                cell_number = int(line[: match.end()].split()[0])
                return cell_number
    raise ValueError(f"Cells with material 0 are not found in {mcnp}. Is it MCNP file?")
