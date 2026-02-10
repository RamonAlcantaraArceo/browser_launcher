"""Unit tests for Safari and Edge browser launcher implementations."""

from pathlib import Path
from unittest import mock
import pytest

from browser_launcher.browsers.safari import SafariLauncher
from browser_launcher.browsers.edge import EdgeLauncher
from browser_launcher.browsers.base import BrowserConfig

@pytest.mark.parametrize("Launcher, browser_name", [
    (SafariLauncher, "safari"),
    (EdgeLauncher, "edge"),
])
def test_launcher_instantiation_and_browser_name(Launcher, browser_name):
    config = BrowserConfig(
        binary_path=None,
        headless=True,
        user_data_dir=None,
        custom_flags=None,
        extra_options={}
    )
    launcher = Launcher(config, mock.Mock())
    assert launcher is not None
    assert launcher.browser_name == browser_name
    args = launcher.build_command_args("https://example.com")
    assert isinstance(args, list)
    assert args == []
