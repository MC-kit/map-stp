from pathlib import Path

import pytest

from mapstp.utils.resource import filename_resolver, path_resolver

THIS_FILENAME = Path(__file__).name


# noinspection PyCompatibility
@pytest.mark.parametrize(
    "package, resource, expected",
    [
        ("tests", "data/test1.stp", "/data/test1.stp"),
    ],
)
def test_filename_resolver(package, resource, expected):
    resolver = filename_resolver(package)
    actual = resolver(resource)
    assert actual.replace("\\", "/").endswith(
        expected
    ), "Failed to compute resource file name"
    assert Path(actual).exists(), f"The resource '{resource}' is not available"


# noinspection PyCompatibility
@pytest.mark.parametrize(
    "package, resource, expected",
    [
        ("tests", "data/not_existing", "tests/data/not_existing"),
        ("mapstp", "data/not_existing", "mapstp/data/not_existing"),
    ],
)
def test_filename_resolver_when_resource_doesnt_exist(package, resource, expected):
    resolver = filename_resolver(package)
    actual = resolver(resource)
    assert not Path(
        actual
    ).exists(), f"The resource '{resource}' should not be available"


def test_filename_resolver_when_package_doesnt_exist():
    resolver = filename_resolver("not_existing")
    with pytest.raises(ModuleNotFoundError):
        resolver("something.txt")


def test_path_resolver():
    resolver = path_resolver("tests")
    actual = resolver("utils/" + THIS_FILENAME)
    assert isinstance(actual, Path)
    assert actual.name == THIS_FILENAME
    assert actual.exists(), f"The file '{THIS_FILENAME}' should be available"


def test_path_resolver_in_own_package_with_separate_file():
    resolver = path_resolver("tests")
    assert resolver("data").exists(), "Should find 'data' in the 'tests' package"


if __name__ == "__main__":
    pytest.main()
