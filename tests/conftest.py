"""Shared pytest fixtures for browser_launcher tests."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import toml

from browser_launcher.browsers.base import BrowserConfig


@pytest.fixture
def mock_browser_config():
    """Mock BrowserLauncherConfig using real default_config.toml content."""
    # Load the actual default config
    default_config_path = (
        Path(__file__).parent.parent
        / "src"
        / "browser_launcher"
        / "assets"
        / "default_config.toml"
    )
    config_data = toml.load(default_config_path)

    with patch("browser_launcher.cli.BrowserLauncherConfig") as mock_config:
        config_instance = MagicMock()
        config_instance.config_data = config_data
        config_instance.get_default_browser.return_value = config_data["general"][
            "default_browser"
        ]
        config_instance.get_default_url.return_value = config_data["urls"]["homepage"]
        config_instance.get_console_logging.return_value = config_data["logging"][
            "console_logging"
        ]
        config_instance.get_logging_level.return_value = config_data["logging"][
            "default_log_level"
        ]

        # Mock get_browser_config to return a valid BrowserConfig
        def mock_get_browser_config(browser_name: str, headless: bool = False):
            browser_data = config_data.get("browsers", {}).get(browser_name, {})
            return BrowserConfig(
                binary_path=None,
                headless=headless or browser_data.get("headless", False),
                user_data_dir=None,
                custom_flags=None,
                extra_options={},
            )

        config_instance.get_browser_config.side_effect = mock_get_browser_config

        mock_config.return_value = config_instance
        yield config_instance
