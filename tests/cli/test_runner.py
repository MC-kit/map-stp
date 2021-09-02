import pytest

from mapstp.cli.runner import VERSION, mapstp, meta


def test_version_command(runner):
    result = runner.invoke(mapstp, args=["--version"], catch_exceptions=False)
    assert result.exit_code == 0, (
        "Should success on '--version' option: " + result.output
    )
    assert VERSION in result.output, "print version on 'version' command"


def test_help_command(runner):
    result = runner.invoke(mapstp, args=["--help"], catch_exceptions=False)
    assert result.exit_code == 0, result.output
    assert "Usage: " in result.output
    expected = meta.__summary__.replace("\n", "")
    actual = result.output.replace("\n", "")
    assert expected in actual


if __name__ == "__main__":
    pytest.main()
