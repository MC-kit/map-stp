from logging import getLogger

import pytest

from mapstp.cli.logging import init_logger


def test_std_logging_interception(capsys):
    init_logger(log_path=None)
    msg = "Test error output"
    getLogger().error(msg)
    err = capsys.readouterr().err


@pytest.mark.xfail
def test_std_logging_interception_with_wrong_level(capsys):
    init_logger(log_path=None)
    msg = "Test error output"
    getLogger().log(100000000, msg)
    err = capsys.readouterr().err
    assert msg in err, f"Should contain message '{msg}'"
