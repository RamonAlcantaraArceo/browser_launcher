"""Tests for Chrome browser implementation."""

import os
import pytest
import unittest.mock as mock
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.base import BrowserConfig


class TestChromeBuildCommandArgs:
    """Test Chrome argument building logic."""

    def test_chrome_command_includes_binary_path(self):
        """Test that binary path is first argument."""
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
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
            binary_path="/usr/bin/google-chrome",
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
            binary_path="/usr/bin/google-chrome",
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
            binary_path="/usr/bin/google-chrome",
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
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir="/tmp/profile",
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        assert "--user-data-dir=/tmp/profile" in args

    def test_chrome_adds_custom_flags(self):
        """Test that custom flags are included."""
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
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
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        args = browser.build_command_args("https://example.com")
        
        # Should have some disable flags for automation
        assert any("disable" in arg.lower() for arg in args)


class TestChromeBinaryValidation:
    """Test Chrome binary path validation."""

    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_chrome_validates_existing_binary(self, mock_exists, mock_access):
        """Test that validate_binary returns True when binary exists and is executable."""
        mock_exists.return_value = True
        mock_access.return_value = True
        
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.validate_binary() is True

    @mock.patch("os.path.exists")
    def test_chrome_rejects_nonexistent_binary(self, mock_exists):
        """Test that validate_binary returns False when binary doesn't exist."""
        mock_exists.return_value = False
        
        config = BrowserConfig(
            binary_path="/nonexistent/chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.validate_binary() is False

    @mock.patch("os.access")
    @mock.patch("os.path.exists")
    def test_chrome_rejects_non_executable_binary(self, mock_exists, mock_access):
        """Test that validate_binary returns False when binary is not executable."""
        mock_exists.return_value = True
        mock_access.return_value = False
        
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.validate_binary() is False


class TestChromeLaunch:
    """Test Chrome launch execution."""

    @mock.patch("subprocess.Popen")
    def test_chrome_launch_calls_subprocess(self, mock_popen):
        """Test that launch() calls subprocess.Popen."""
        mock_process = mock.Mock()
        mock_popen.return_value = mock_process
        
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        result = browser.launch("https://example.com")
        
        assert result == mock_process
        mock_popen.assert_called_once()

    @mock.patch("subprocess.Popen", side_effect=OSError("Cannot find binary"))
    def test_chrome_launch_propagates_subprocess_error(self, mock_popen):
        """Test that launch() propagates subprocess errors."""
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        
        with pytest.raises(OSError):
            browser.launch("https://example.com")

    @mock.patch("subprocess.Popen")
    def test_chrome_launch_returns_process_object(self, mock_popen):
        """Test that launch() returns the process object."""
        mock_process = mock.Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        result = browser.launch("https://example.com")
        
        assert result.pid == 12345


class TestChromeBrowserName:
    """Test Chrome browser identification."""

    def test_chrome_browser_name_property(self):
        """Test that browser_name returns 'chrome'."""
        config = BrowserConfig(
            binary_path="/usr/bin/google-chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        browser = ChromeLauncher(config, mock.Mock())
        assert browser.browser_name == "chrome"
