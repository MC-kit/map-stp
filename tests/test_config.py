from __future__ import annotations

from os import environ

import pytest

from mapstp.config import env

TEST_VALUE = "_TEST_VALUE"


@pytest.fixture()
def setval():
    def _call(env_value):
        if env_value is not None:
            environ[TEST_VALUE] = env_value

    yield _call

    if TEST_VALUE in environ:
        del environ[TEST_VALUE]


@pytest.mark.parametrize(
    "env_value,type_,default,expected,msg",
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
def test_env(setval, env_value, type_, default, expected, msg):  # noqa: PLR0913
    setval(env_value)
    actual = env(TEST_VALUE, type_, default)
    assert actual is None and expected is None or actual == expected


@pytest.mark.parametrize(
    "env_value,type_,default,exception,msg",
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
def test_env_bad_paths(setval, env_value, type_, default, exception, msg):  # noqa: PLR0913
    setval(env_value)
    with pytest.raises(exception):
        env(TEST_VALUE, type_, default)
