"""Unit tests for Firefox browser launcher implementation."""

# import subprocess  # No longer needed with WebDriver-based launcher
from pathlib import Path
from unittest import mock

import pytest

from browser_launcher.browsers.base import BrowserConfig
from browser_launcher.browsers.firefox import FirefoxLauncher


class TestFirefoxLauncher:
    """Test suite for FirefoxLauncher implementation."""

    @pytest.fixture
    def firefox_config(self):
        """Create a basic Firefox configuration for testing."""
        return BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=False,
            user_data_dir=None,
            custom_flags=[],
        )

    @pytest.fixture
    def firefox_headless_config(self):
        """Create a headless Firefox configuration for testing."""
        return BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=True,
            user_data_dir=None,
            custom_flags=[],
        )

    def test_firefox_launcher_is_instantiable(self, firefox_config):
        """Test that FirefoxLauncher can be instantiated with valid config."""
        launcher = FirefoxLauncher(firefox_config, mock.Mock())
        assert launcher is not None
        assert isinstance(launcher, FirefoxLauncher)

    def test_browser_name_property_returns_firefox(self, firefox_config):
        """Test that browser_name property returns 'firefox'."""
        launcher = FirefoxLauncher(firefox_config, mock.Mock())
        assert launcher.browser_name == "firefox"

    def test_build_command_args_basic(self, firefox_config):
        """Test build_command_args() returns list starting with binary path."""
        launcher = FirefoxLauncher(firefox_config, mock.Mock())
        args = launcher.build_command_args("")
        assert isinstance(args, list)
        assert len(args) > 0
        assert args[0] == "/usr/bin/firefox"

    def test_build_command_args_headless_flag(self, firefox_headless_config):
        """Test build_command_args() includes -headless flag when headless=True."""
        launcher = FirefoxLauncher(firefox_headless_config, mock.Mock())
        args = launcher.build_command_args("")
        assert "-headless" in args

    def test_build_command_args_no_headless_flag_when_false(self, firefox_config):
        """Test build_command_args() excludes -headless flag when headless=False."""
        launcher = FirefoxLauncher(firefox_config, mock.Mock())
        args = launcher.build_command_args("")
        assert "-headless" not in args

    def test_build_command_args_with_user_data_dir(self):
        """Test build_command_args() includes profile path for user_data_dir."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=False,
            user_data_dir=Path("/home/user/.mozilla/firefox/profile"),
            custom_flags=[],
        )
        launcher = FirefoxLauncher(config, mock.Mock())
        args = launcher.build_command_args("")
        assert "-profile" in args
        profile_idx = args.index("-profile")
        assert args[profile_idx + 1] == "/home/user/.mozilla/firefox/profile"

    def test_build_command_args_with_custom_flags(self):
        """Test build_command_args() includes custom flags."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=False,
            user_data_dir=None,
            custom_flags=["--width=1920", "--height=1080"],
        )
        launcher = FirefoxLauncher(config, mock.Mock())
        args = launcher.build_command_args("")
        assert "--width=1920" in args
        assert "--height=1080" in args

    def test_build_command_args_with_custom_and_headless_flags(self):
        """Test build_command_args() combines custom and headless flags."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=True,
            user_data_dir=None,
            custom_flags=["--width=1920"],
        )
        launcher = FirefoxLauncher(config, mock.Mock())
        args = launcher.build_command_args("")
        assert "-headless" in args
        assert "--width=1920" in args

    def test_build_command_args_with_extra_options(self):
        """Test build_command_args() with extra_options dict."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/firefox"),
            headless=False,
            user_data_dir=None,
            custom_flags=[],
            extra_options={"pref": "browser.startup.homepage", "value": "about:blank"},
        )
        launcher = FirefoxLauncher(config, mock.Mock())
        args = launcher.build_command_args("")
        # Should include the binary path and not error out
        assert args[0] == "/usr/bin/firefox"
