"""Unit tests for utils.py."""

import pytest

from browser_launcher.utils import get_command_context


@pytest.mark.unit
def test_get_command_context():
    ctx = get_command_context(
        "launch", {"browser": "chrome", "headless": True, "foo": None}
    )
    assert ctx == "[launch] browser=chrome | headless=True"
    ctx2 = get_command_context("init")
    assert ctx2 == "[init]"
