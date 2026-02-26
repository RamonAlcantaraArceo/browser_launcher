"""Tests for Edge browser implementation."""

import os
import unittest.mock as mock
from pathlib import Path

import pytest

from browser_launcher.browsers.base import BrowserConfig, BrowserLauncher
from browser_launcher.browsers.edge import EdgeLauncher


@pytest.mark.smoke
class TestEdgeBrowserName:
    """Test suite for EdgeLauncher implementation."""

    @pytest.fixture
    def edge_config(self):
        """Create a basic Edge configuration for testing."""
        # Use headless mode in CI, allow headfull locally for debugging
        is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
        return BrowserConfig(
            binary_path=Path("/usr/bin/edge"),
            headless=is_ci,  # Dynamic based on environment
            user_data_dir=None,
            custom_flags=[],
        )

    @pytest.fixture
    def edge_instance(self, edge_config: BrowserConfig):
        launcher = EdgeLauncher(edge_config, mock.Mock())
        yield launcher

        if launcher.driver:
            try:
                launcher.driver.close()
            except:  # noqa: E722
                pass

    def test_edge_launcher_is_instantiable(self, edge_instance: BrowserLauncher):
        """Test that EdgeLauncher can be instantiated with valid config."""

        assert edge_instance is not None
        assert isinstance(edge_instance, EdgeLauncher)

    def test_browser_name_property_returns_edge(self, edge_instance: BrowserLauncher):
        """Test that browser_name property returns 'edge'."""

        assert edge_instance.browser_name == "edge"

    def test_has_driver_property(self, edge_instance: BrowserLauncher):
        edge_instance.launch("about:blank")
        assert edge_instance.driver
        pass

    def test_failed_to_launch(self, edge_instance: BrowserLauncher):
        """Test that mocks the webdriver.Edge constructor and raises a
        WebDriverException simulating a missing driver scenario."""
        import selenium.webdriver
        from selenium.common.exceptions import WebDriverException

        # Patch Edge WebDriver to raise exception
        with (
            mock.patch.object(
                selenium.webdriver,
                "Edge",
                side_effect=WebDriverException("Driver not found"),
            ),
            pytest.raises(WebDriverException),
        ):
            edge_instance._driver = None
            # Should log error and not raise
            edge_instance.launch("about:blank")
            # After failed launch, driver should still be None
            assert edge_instance.driver is None
