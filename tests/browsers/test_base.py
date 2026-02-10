"""Tests for browser base class and BrowserConfig."""

import pytest
import unittest.mock as mock
from browser_launcher.browsers.base import BrowserLauncher, BrowserConfig


class TestBrowserLauncherInterface:
    """Define the contract all browser implementations must follow."""

    def test_browser_launcher_is_abstract(self):
        """Base class cannot be instantiated directly."""
        config = BrowserConfig(
            binary_path=None,
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        with pytest.raises(TypeError):
            BrowserLauncher(config, mock.Mock())

    def test_browser_launcher_requires_launch_implementation(self):
        """All browsers must implement launch()."""
        class IncompleteChrome(BrowserLauncher):
            def validate_binary(self):
                return True

            def build_command_args(self, url):
                return []

            @property
            def browser_name(self):
                return "chrome"
            # Missing launch()

        with pytest.raises(TypeError):
            IncompleteChrome(
                BrowserConfig(
                    binary_path=None,
                    headless=False,
                    user_data_dir=None,
                    custom_flags=None
                ),
                mock.Mock()
            )

    def test_browser_launcher_requires_validate_binary(self):
        """All browsers must implement validate_binary()."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url):
                return mock.Mock()

            def build_command_args(self, url):
                return []

            @property
            def browser_name(self):
                return "chrome"
            # Missing validate_binary()

        with pytest.raises(TypeError):
            IncompleteChrome(
                BrowserConfig(
                    binary_path=None,
                    headless=False,
                    user_data_dir=None,
                    custom_flags=None
                ),
                mock.Mock()
            )

    def test_browser_launcher_requires_build_command_args(self):
        """All browsers must implement build_command_args()."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url):
                return mock.Mock()

            def validate_binary(self):
                return True

            @property
            def browser_name(self):
                return "chrome"
            # Missing build_command_args()

        with pytest.raises(TypeError):
            IncompleteChrome(
                BrowserConfig(
                    binary_path=None,
                    headless=False,
                    user_data_dir=None,
                    custom_flags=None
                ),
                mock.Mock()
            )

    def test_browser_launcher_requires_browser_name_property(self):
        """All browsers must implement browser_name property."""
        class IncompleteChrome(BrowserLauncher):
            def launch(self, url):
                return mock.Mock()

            def validate_binary(self):
                return True

            def build_command_args(self, url):
                return []
            # Missing browser_name property

        with pytest.raises(TypeError):
            IncompleteChrome(
                BrowserConfig(
                    binary_path=None,
                    headless=False,
                    user_data_dir=None,
                    custom_flags=None
                ),
                mock.Mock()
            )


class TestBrowserConfig:
    """Test BrowserConfig data structure."""

    def test_browser_config_stores_binary_path(self):
        """Test that BrowserConfig stores binary_path."""
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        assert config.binary_path == "/usr/bin/chrome"

    def test_browser_config_stores_headless_mode(self):
        """Test that BrowserConfig stores headless mode."""
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=True,
            user_data_dir=None,
            custom_flags=None
        )
        assert config.headless is True

    def test_browser_config_stores_user_data_dir(self):
        """Test that BrowserConfig stores user_data_dir."""
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=False,
            user_data_dir="/tmp/profile",
            custom_flags=None
        )
        assert config.user_data_dir == "/tmp/profile"

    def test_browser_config_stores_custom_flags(self):
        """Test that BrowserConfig stores custom_flags."""
        flags = ["--disable-sync", "--no-first-run"]
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=flags
        )
        assert config.custom_flags == flags

    def test_browser_config_stores_none_values(self):
        """Test that BrowserConfig handles None values."""
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        assert config.user_data_dir is None
        assert config.custom_flags is None

    def test_browser_config_headless_false_by_default(self):
        """Test that BrowserConfig can be created with headless=False."""
        config = BrowserConfig(
            binary_path="/usr/bin/chrome",
            headless=False,
            user_data_dir=None,
            custom_flags=None
        )
        assert config.headless is False
