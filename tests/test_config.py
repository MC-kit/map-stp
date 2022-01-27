from os import environ

import pytest

from mapstp.config import env

TEST_VALUE = "_TEST_VALUE"


@pytest.fixture
def setval():
    def _call(value):
        if value is not None:
            environ[TEST_VALUE] = value

    yield _call
    if TEST_VALUE in environ:
        del environ[TEST_VALUE]


@pytest.mark.parametrize(
    "value,type_,default,expected,msg",
    [
        (
            None,
            str,
            "aaa",
            "aaa",
            "If variable is not set and default is provided, then return the default",
        ),
        (
            None,
            str,
            None,
            None,
            "If variable is not set and no default is provided, then return None",
        ),
        ("1", str, None, "1", "return str"),
        ("1", int, None, 1, "return int"),
        ("1", float, None, 1.0, "return float"),
        ("1", complex, None, 1.0 + 0j, "return complex"),
        ("on", bool, None, True, "return True if 'on' is set"),
        ("no", bool, None, False, "return False if 'no' is set"),
    ],
)
def test_env(setval, value, type_, default, expected, msg):
    setval(value)
    actual = env(TEST_VALUE, type_, default)
    assert actual == expected


@pytest.mark.parametrize(
    "value,type_,default,exception,msg",
    [
        ("bad", bool, None, ValueError, "'bad' is invalid value for boolean variable"),
        ("bad", int, None, ValueError, "'bad' is invalid value for int variable"),
        ("bad", float, None, ValueError, "'bad' is invalid value for float variable"),
        (
            "bad",
            complex,
            None,
            ValueError,
            "'bad' is invalid value for complex variable",
        ),
    ],
)
def test_env_bad_paths(setval, value, type_, default, exception, msg):
    setval(value)
    with pytest.raises(exception):
        env(TEST_VALUE, type_, default)
