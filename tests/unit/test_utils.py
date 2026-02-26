"""Unit tests for utils.py."""

from browser_launcher.utils import get_command_context


def test_get_command_context():
    ctx = get_command_context(
        "launch", {"browser": "chrome", "headless": True, "foo": None}
    )
    assert ctx == "[launch] browser=chrome | headless=True"
    ctx2 = get_command_context("init")
    assert ctx2 == "[init]"
