"""Unified tests for all browser launcher implementations:
Chrome, Firefox, Safari, Edge."""

from pathlib import Path
from unittest import mock

import pytest

from browser_launcher.browsers.base import BrowserConfig
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.edge import EdgeLauncher
from browser_launcher.browsers.firefox import FirefoxLauncher
from browser_launcher.browsers.safari import SafariLauncher


@pytest.mark.parametrize(
    "Launcher, browser_name, config, headless_flag",
    [
        # Chrome
        (
            ChromeLauncher,
            "chrome",
            BrowserConfig(
                binary_path=Path("/usr/bin/google-chrome"),
                headless=True,
                user_data_dir=Path("/tmp/profile"),
                custom_flags=["--test-flag"],
                extra_options={},
            ),
            "--headless",
        ),
        # Firefox
        (
            FirefoxLauncher,
            "firefox",
            BrowserConfig(
                binary_path=Path("/usr/bin/firefox"),
                headless=True,
                user_data_dir=Path("/tmp/profile"),
                custom_flags=["--test-flag"],
                extra_options={},
            ),
            "-headless",
        ),
        # Safari (WebDriver, args always empty)
        (
            SafariLauncher,
            "safari",
            BrowserConfig(
                binary_path=None,
                headless=True,
                user_data_dir=None,
                custom_flags=None,
                extra_options={},
            ),
            None,
        ),
        # Edge (WebDriver, args always empty)
        (
            EdgeLauncher,
            "edge",
            BrowserConfig(
                binary_path=None,
                headless=True,
                user_data_dir=None,
                custom_flags=None,
                extra_options={},
            ),
            None,
        ),
    ],
)
def test_launcher_instantiation_and_args(Launcher, browser_name, config, headless_flag):
    launcher = Launcher(config, mock.Mock())
    assert launcher is not None
    assert launcher.browser_name == browser_name
