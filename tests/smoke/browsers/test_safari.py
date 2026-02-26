"""Tests for Safari browser implementation."""

import sys
import unittest.mock as mock
from pathlib import Path

import pytest

from browser_launcher.browsers.base import BrowserConfig, BrowserLauncher
from browser_launcher.browsers.safari import SafariLauncher


@pytest.mark.smoke
@pytest.mark.skipif(
    sys.platform != "darwin", reason="Safari is only available on macOS"
)
class TestSafariBrowserName:
    """Test suite for SafariLauncher implementation."""

    @pytest.fixture
    def safari_config(self):
        """Create a basic Safari configuration for testing."""
        return BrowserConfig(
            binary_path=Path("/usr/bin/safari"),
            headless=False,
            user_data_dir=None,
            custom_flags=[],
        )

    @pytest.fixture
    def safari_instance(self, safari_config: BrowserConfig):
        launcher = SafariLauncher(safari_config, mock.Mock())
        yield launcher

        if launcher.driver:
            try:
                launcher.driver.close()
            except:  # noqa: E722
                pass

    def test_safari_launcher_is_instantiable(self, safari_instance: BrowserLauncher):
        """Test that SafariLauncher can be instantiated with valid config."""

        assert safari_instance is not None
        assert isinstance(safari_instance, SafariLauncher)

    def test_browser_name_property_returns_safari(
        self, safari_instance: BrowserLauncher
    ):
        """Test that browser_name property returns 'safari'."""

        assert safari_instance.browser_name == "safari"

    def test_has_driver_property(self, safari_instance: BrowserLauncher):
        safari_instance.launch("about:blank")
        assert safari_instance.driver

    def test_failed_to_launch(self, safari_instance: BrowserLauncher):
        """Test that mocks the webdriver.Safari constructor and raises a
        WebDriverException simulating a missing driver scenario."""
        import selenium.webdriver
        from selenium.common.exceptions import WebDriverException

        # Patch Safari WebDriver to raise exception
        with (
            mock.patch.object(
                selenium.webdriver,
                "Safari",
                side_effect=WebDriverException("Driver not found"),
            ),
            pytest.raises(WebDriverException),
        ):
            safari_instance._driver = None
            # Should log error and not raise
            safari_instance.launch("about:blank")
            # After failed launch, driver should still be None
            assert safari_instance.driver is None
