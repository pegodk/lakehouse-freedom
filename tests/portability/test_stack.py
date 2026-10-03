"""End-to-end on the running OpenLakehouse stack at SF0.01 (make test-stack)."""

import pytest

pytestmark = pytest.mark.stack


def test_pipeline_check_and_freedom_day():
    from freedom.cli import main

    assert main(["pipeline", "--scale", "0.01"]) == 0
    assert main(["benchmark", "--scale", "0.01", "--repeats", "1"]) == 0
    assert main(["day", "--scale", "0.01"]) == 0
    assert main(["check", "--scale", "0.01"]) == 0
