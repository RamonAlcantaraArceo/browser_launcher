"""Unit tests for Firefox browser launcher implementation."""

# import subprocess  # No longer needed with WebDriver-based launcher
from pathlib import Path
from unittest import mock

import pytest

from browser_launcher.browsers.base import BrowserConfig, BrowserLauncher
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
    def firefox_instance(self, firefox_config: BrowserConfig):
        launcher = FirefoxLauncher(firefox_config, mock.Mock())
        yield launcher

        if launcher.driver:
            try:
                launcher.driver.close()
            except:  # noqa: E722
                pass

    def test_firefox_launcher_is_instantiable(self, firefox_instance: BrowserLauncher):
        """Test that FirefoxLauncher can be instantiated with valid config."""

        assert firefox_instance is not None
        assert isinstance(firefox_instance, FirefoxLauncher)

    def test_browser_name_property_returns_firefox(
        self, firefox_instance: BrowserLauncher
    ):
        """Test that browser_name property returns 'firefox'."""

        assert firefox_instance.browser_name == "firefox"

    def test_has_driver_property(self, firefox_instance: BrowserLauncher):
        firefox_instance.launch("about:blank")
        assert firefox_instance.driver

    def test_failed_to_launch(self, firefox_instance: BrowserLauncher):
        """Test that mocks the webdriver.Firefox constructor and raises a
        WebDriverException simulating a missing driver scenario."""
        import selenium.webdriver
        from selenium.common.exceptions import WebDriverException

        # Patch Firefox WebDriver to raise exception
        with (
            mock.patch.object(
                selenium.webdriver,
                "Firefox",
                side_effect=WebDriverException("Driver not found"),
            ),
            pytest.raises(WebDriverException),
        ):
            firefox_instance._driver = None
            # Should log error and not raise
            firefox_instance.launch("about:blank")
            # After failed launch, driver should still be None
            assert firefox_instance.driver is None
