from typing import Generator, Iterable, List, TextIO

import re

_CELL_START_PATTERN = re.compile(r"^\s{0,5}\d.*")
_CELLS_END_PATTERN = re.compile(r"^\s*$")


def merge_lines(
    paths: List[List[str]], mcnp_lines: Iterable[str], separator: str = "/"
) -> Generator[str, None, None]:

    first_cell = True
    cells_over = False
    current_path_idx = 0

    def format_comment():
        nonlocal current_path_idx
        comment = f"      $ stp: {separator.join(paths[current_path_idx])}\n"
        current_path_idx += 1
        return comment

    for line in mcnp_lines:
        if not cells_over:
            if _CELLS_END_PATTERN.match(line):
                if first_cell:
                    raise ValueError(f"Incorrect MCNP file: cannot find cells")
                if current_path_idx < len(paths):
                    yield format_comment()
                assert (
                    len(paths) <= current_path_idx
                ), f"Only {current_path_idx} merged, expected  {len(paths)}"
                cells_over = True
        if cells_over or len(paths) <= current_path_idx:
            yield line
        elif first_cell:
            if _CELL_START_PATTERN.match(line):
                first_cell = False
            yield line
        else:
            if _CELL_START_PATTERN.match(line):
                yield format_comment()
            yield line


def merge_paths(
    output: TextIO, paths: List[List[str]], mcnp, separator: str = "/"
) -> None:
    with mcnp.open(encoding="cp1251") as mcnp_stream:
        for line in merge_lines(paths, mcnp_stream.readlines(), separator):
            print(line, file=output, end="")
