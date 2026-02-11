"""Tests for Chrome browser implementation."""

import unittest.mock as mock
from pathlib import Path

import pytest

from browser_launcher.browsers.base import BrowserConfig, BrowserLauncher
from browser_launcher.browsers.chrome import ChromeLauncher


class TestChromeBrowserName:
    """Test suite for ChromeLauncher implementation."""

    @pytest.fixture
    def chrome_config(self):
        """Create a basic Chrome configuration for testing."""
        return BrowserConfig(
            binary_path=Path("/usr/bin/chrome"),
            headless=False,
            user_data_dir=None,
            custom_flags=[],
        )

    @pytest.fixture
    def chrome_instance(self, chrome_config: BrowserConfig):
        launcher = ChromeLauncher(chrome_config, mock.Mock())
        yield launcher

        if launcher.driver:
            try:
                launcher.driver.close()
            except:  # noqa: E722
                pass

    def test_chrome_launcher_is_instantiable(self, chrome_instance: BrowserLauncher):
        """Test that ChromeLauncher can be instantiated with valid config."""

        assert chrome_instance is not None
        assert isinstance(chrome_instance, ChromeLauncher)

    def test_browser_name_property_returns_chrome(
        self, chrome_instance: BrowserLauncher
    ):
        """Test that browser_name property returns 'chrome'."""

        assert chrome_instance.browser_name == "chrome"

    def test_has_driver_property(self, chrome_instance: BrowserLauncher):
        chrome_instance.launch("about:blank")

    def test_has_driver_removed_halfway(self, chrome_instance: BrowserLauncher):
        chrome_instance.launch("about:blank")
        assert chrome_instance.driver
        chrome_instance.driver.close()
        chrome_instance._driver = None

        chrome_instance.safe_get_address("about:blank")
        pass

    def test_failed_to_launch(self, chrome_instance: BrowserLauncher):
        """Test that mocks the webdriver.Chrome constructor and raises a
        WebDriverException simulating a missing driver scenario."""
        import selenium.webdriver
        from selenium.common.exceptions import WebDriverException

        # Patch Chrome WebDriver to raise exception
        with (
            mock.patch.object(
                selenium.webdriver,
                "Chrome",
                side_effect=WebDriverException("Driver not found"),
            ),
            pytest.raises(WebDriverException),
        ):
            chrome_instance._driver = None
            # Should log error and not raise
            chrome_instance.launch("about:blank")
            # After failed launch, driver should still be None
            assert chrome_instance.driver is None
