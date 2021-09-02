import pytest

from mapstp.cli.runner import VERSION, mapstp


def test_version_command(runner):
    result = runner.invoke(mapstp, args=["--version"], catch_exceptions=False)
    assert result.exit_code == 0, (
        "Should success on '--version' option: " + result.output
    )
    assert VERSION in result.output, "print version on 'version' command"


if __name__ == "__main__":
    pytest.main()
