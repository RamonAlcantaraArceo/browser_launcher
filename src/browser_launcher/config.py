"""Configuration management for browser launcher."""

import toml
from pathlib import Path
from typing import Optional
from browser_launcher.browsers.base import BrowserConfig

class BrowserLauncherConfig:
    """Load and manage browser launcher configuration from TOML."""
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path.home() / ".browser_launcher" / "config.toml")
        self.config_data = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        return toml.load(self.config_path)

    def get_browser_config(self, browser_name: str, headless: bool = False) -> BrowserConfig:
        browsers = self.config_data.get("browsers", {})
        browser_section = browsers.get(browser_name, {})
        binary_path = browser_section.get("binary_path")
        user_data_dir = browser_section.get("user_data_dir")
        custom_flags = browser_section.get("custom_flags")
        extra_options = browser_section.get("extra_options", {})
        return BrowserConfig(
            binary_path=binary_path,
            headless=headless or browser_section.get("headless", False),
            user_data_dir=user_data_dir,
            custom_flags=custom_flags,
            extra_options=extra_options,
        )

    def get_default_browser(self) -> str:
        return self.config_data.get("general", {}).get("default_browser", "chrome")

    def get_default_url(self) -> str:
        return self.config_data.get("urls", {}).get("homepage", "https://www.microsoft.com")
