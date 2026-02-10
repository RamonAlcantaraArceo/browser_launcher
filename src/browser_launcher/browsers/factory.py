"""BrowserFactory for instantiating browser launchers."""

from typing import Type
from browser_launcher.browsers.base import BrowserLauncher, BrowserConfig
from browser_launcher.browsers.chrome import ChromeLauncher
from browser_launcher.browsers.firefox import FirefoxLauncher
from browser_launcher.browsers.safari import SafariLauncher
from browser_launcher.browsers.edge import EdgeLauncher

class BrowserFactory:
    """Factory for creating browser launcher instances."""
    _browsers = {
        "chrome": ChromeLauncher,
        "firefox": FirefoxLauncher,
        "safari": SafariLauncher,
        "edge": EdgeLauncher,
    }

    @classmethod
    def create(cls, browser_name: str, config: BrowserConfig, logger) -> BrowserLauncher:
        """Create and return a browser launcher instance."""
        if browser_name not in cls._browsers:
            raise ValueError(f"Unsupported browser: {browser_name}")
        browser_class: Type[BrowserLauncher] = cls._browsers[browser_name]
        return browser_class(config, logger)

    @classmethod
    def get_available_browsers(cls):
        """Return list of supported browser names."""
        return list(cls._browsers.keys())
