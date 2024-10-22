from __future__ import annotations

from logging import WARNING, LogRecord, getLogger

from mapstp.cli.mapstp_logging import InterceptHandler, init_logger


def test_std_logging_interception(capsys):
    init_logger(log_path=None)
    msg = "Test error output"
    getLogger().error(msg)
    err = capsys.readouterr().err
    assert msg in err, f"STD error output should contain message: {msg}"


def test_when_stderr_is_off(capsys):
    init_logger(stderr_format=None, log_path=None)
    msg = "Test error output"
    getLogger().error(msg)
    err = capsys.readouterr().err
    assert not err, "STD error output should not contain any message"


class _Record(LogRecord):
    def __init__(self):
        super().__init__(
            name="UNKNOWN_LEVEL",
            level=WARNING,
            pathname=__file__,
            lineno=20,
            msg="Test record",
            args=None,
            exc_info=None,
        )
        self.levelname = self.name


def test_std_logging_interception_with_wrong_level(capsys):
    init_logger(log_path=None)
    handler = InterceptHandler()
    record = _Record()
    handler.emit(record)
    err = capsys.readouterr().err
    msg = record.msg
    assert msg in err, f"STD error output should contain message: {msg}"
