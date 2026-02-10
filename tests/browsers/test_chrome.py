"""Tests for Chrome browser implementation."""

import os
from pathlib import Path
import pytest
import unittest.mock as mock
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.base import BrowserConfig


class TestChromeBuildCommandArgs:
    """Test Chrome argument building logic."""

    def test_chrome_command_includes_binary_path(self):
        """Test that binary path is first argument."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[0] == "/usr/bin/google-chrome"

    def test_chrome_command_includes_url_as_last_arg(self):
        """Test that URL is last argument."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert args[-1] == "https://example.com"

    def test_chrome_headless_adds_flag(self):
        """Test that --headless flag is added when headless=True."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=True,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--headless" in args

    def test_chrome_no_headless_excludes_flag(self):
        """Test that --headless flag is not added when headless=False."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--headless" not in args

    def test_chrome_adds_user_data_dir(self):
        """Test that user data directory flag is added."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=Path("/tmp/profile"),
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--user-data-dir=/tmp/profile" in args

    def test_chrome_adds_custom_flags(self):
        """Test that custom flags are included."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=["--disable-sync", "--no-first-run"]
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--disable-sync" in args
        assert "--no-first-run" in args

    def test_chrome_includes_default_flags(self):
        """Test that Chrome includes sensible default flags."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        
        # Should have some disable flags for automation
        assert any("disable" in arg.lower() for arg in args)


class TestChromeBrowserName:
    """Test Chrome browser identification."""

    def test_chrome_browser_name_property(self):
        """Test that browser_name returns 'chrome'."""
        config = BrowserConfig(
            binary_path=Path("/usr/bin/google-chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.browser_name == "chrome"
