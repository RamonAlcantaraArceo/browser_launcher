"""Unit tests for Firefox browser launcher implementation."""

import subprocess
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from browser_launcher.browsers.firefox import FirefoxLauncher
from browser_launcher.browsers.base import BrowserConfig


class TestFirefoxLauncher:
    """Test suite for FirefoxLauncher implementation."""

    @pytest.fixture
    def firefox_config(self):
        """Create a basic Firefox configuration for testing."""
        return BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir=None,
            custom_flags=[],
        )

    @pytest.fixture
    def firefox_headless_config(self):
        """Create a headless Firefox configuration for testing."""
        return BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=True,
            user_data_dir=None,
            custom_flags=[],
        )

    def test_firefox_launcher_is_instantiable(self, firefox_config):
        """Test that FirefoxLauncher can be instantiated with valid config."""
        launcher = FirefoxLauncher(firefox_config)
        assert launcher is not None
        assert isinstance(launcher, FirefoxLauncher)

    def test_browser_name_property_returns_firefox(self, firefox_config):
        """Test that browser_name property returns 'firefox'."""
        launcher = FirefoxLauncher(firefox_config)
        assert launcher.browser_name == "firefox"

    def test_validate_binary_with_existing_executable(self, firefox_config):
        """Test validate_binary() succeeds with existing executable file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            firefox_path = Path(temp_dir) / "firefox"
            firefox_path.touch(mode=0o755)

            config = BrowserConfig(
                binary_path=str(firefox_path),
                headless=False,
                user_data_dir=None,
                custom_flags=[],
            )
            launcher = FirefoxLauncher(config)
            # Should not raise an exception
            launcher.validate_binary()

    def test_validate_binary_with_nonexistent_file(self, firefox_config):
        """Test validate_binary() raises error for non-existent binary."""
        config = BrowserConfig(
            binary_path="/nonexistent/path/to/firefox",
            headless=False,
            user_data_dir=None,
            custom_flags=[],
        )
        launcher = FirefoxLauncher(config)
        with pytest.raises(FileNotFoundError):
            launcher.validate_binary()

    def test_validate_binary_with_non_executable_file(self, firefox_config):
        """Test validate_binary() raises error for non-executable file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            firefox_path = Path(temp_dir) / "firefox"
            firefox_path.touch(mode=0o644)  # No execute permission

            config = BrowserConfig(
                binary_path=str(firefox_path),
                headless=False,
                user_data_dir=None,
                custom_flags=[],
            )
            launcher = FirefoxLauncher(config)
            with pytest.raises(PermissionError):
                launcher.validate_binary()

    def test_build_command_args_basic(self, firefox_config):
        """Test build_command_args() returns list starting with binary path."""
        launcher = FirefoxLauncher(firefox_config)
        args = launcher.build_command_args()
        assert isinstance(args, list)
        assert len(args) > 0
        assert args[0] == "/usr/bin/firefox"

    def test_build_command_args_headless_flag(self, firefox_headless_config):
        """Test build_command_args() includes -headless flag when headless=True."""
        launcher = FirefoxLauncher(firefox_headless_config)
        args = launcher.build_command_args()
        assert "-headless" in args

    def test_build_command_args_no_headless_flag_when_false(self, firefox_config):
        """Test build_command_args() excludes -headless flag when headless=False."""
        launcher = FirefoxLauncher(firefox_config)
        args = launcher.build_command_args()
        assert "-headless" not in args

    def test_build_command_args_with_user_data_dir(self):
        """Test build_command_args() includes profile path for user_data_dir."""
        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir="/home/user/.mozilla/firefox/profile",
            custom_flags=[],
        )
        launcher = FirefoxLauncher(config)
        args = launcher.build_command_args()
        assert "-profile" in args
        profile_idx = args.index("-profile")
        assert args[profile_idx + 1] == "/home/user/.mozilla/firefox/profile"

    def test_build_command_args_with_custom_flags(self):
        """Test build_command_args() includes custom flags."""
        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir=None,
            custom_flags=["--width=1920", "--height=1080"],
        )
        launcher = FirefoxLauncher(config)
        args = launcher.build_command_args()
        assert "--width=1920" in args
        assert "--height=1080" in args

    def test_build_command_args_with_custom_and_headless_flags(self):
        """Test build_command_args() combines custom and headless flags."""
        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=True,
            user_data_dir=None,
            custom_flags=["--width=1920"],
        )
        launcher = FirefoxLauncher(config)
        args = launcher.build_command_args()
        assert "-headless" in args
        assert "--width=1920" in args

    def test_build_command_args_with_extra_options(self):
        """Test build_command_args() with extra_options dict."""
        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir=None,
            custom_flags=[],
            extra_options={"pref": "browser.startup.homepage", "value": "about:blank"},
        )
        launcher = FirefoxLauncher(config)
        args = launcher.build_command_args()
        # Should include the binary path and not error out
        assert args[0] == "/usr/bin/firefox"

    @mock.patch("browser_launcher.browsers.firefox.FirefoxLauncher.validate_binary")
    @mock.patch("subprocess.Popen")
    def test_launch_calls_subprocess_popen(self, mock_popen, mock_validate, firefox_config):
        """Test launch() calls subprocess.Popen with built command args."""
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process

        launcher = FirefoxLauncher(firefox_config)
        result = launcher.launch()

        mock_validate.assert_called_once()
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        # First positional argument should be the command list
        assert isinstance(args[0], list)
        assert args[0][0] == "/usr/bin/firefox"
        # Return value should be the popen process
        assert result == mock_process

    @mock.patch("browser_launcher.browsers.firefox.FirefoxLauncher.validate_binary")
    @mock.patch("subprocess.Popen")
    def test_launch_with_headless(self, mock_popen, mock_validate, firefox_headless_config):
        """Test launch() with headless configuration."""
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process

        launcher = FirefoxLauncher(firefox_headless_config)
        result = launcher.launch()

        mock_validate.assert_called_once()
        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        assert "-headless" in args[0]
        assert result == mock_process

    @mock.patch("browser_launcher.browsers.firefox.FirefoxLauncher.validate_binary")
    @mock.patch("subprocess.Popen")
    def test_launch_with_user_data_dir(self, mock_popen, mock_validate):
        """Test launch() includes profile path in command."""
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process

        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir="/home/user/.mozilla/firefox/profile",
            custom_flags=[],
        )
        launcher = FirefoxLauncher(config)
        result = launcher.launch()

        mock_validate.assert_called_once()
        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        assert "-profile" in args[0]
        assert "/home/user/.mozilla/firefox/profile" in args[0]

    @mock.patch("browser_launcher.browsers.firefox.FirefoxLauncher.validate_binary")
    @mock.patch("subprocess.Popen")
    def test_launch_with_custom_flags(self, mock_popen, mock_validate):
        """Test launch() includes custom flags in command."""
        mock_process = mock.MagicMock()
        mock_popen.return_value = mock_process

        config = BrowserConfig(
            binary_path="/usr/bin/firefox",
            headless=False,
            user_data_dir=None,
            custom_flags=["--private-window"],
        )
        launcher = FirefoxLauncher(config)
        result = launcher.launch()

        mock_validate.assert_called_once()
        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        assert "--private-window" in args[0]
