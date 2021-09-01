from pathlib import Path

from map_stp import __version__


def find_version_from_project_toml():
    toml_path = Path(__file__).parent.parent / "pyproject.toml"
    assert toml_path.exists()
    with toml_path.open() as stream:
        for line in stream:
            line = line.strip()
            if line.startswith("version"):
                version = line.split("=")[1].strip().strip('"')
                return version
        raise ValueError(f"Cannot find item 'version' in {toml_path}")


def test_package():
    version = find_version_from_project_toml()
    assert __version__ == version
