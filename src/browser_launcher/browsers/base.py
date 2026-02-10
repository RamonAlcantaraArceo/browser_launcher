"""Browser base class and configuration."""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class BrowserConfig:
    """Configuration for a browser instance."""

    binary_path: Optional[Path]
    headless: bool
    user_data_dir: Optional[Path]
    custom_flags: Optional[List[str]]
    extra_options: Dict[str, Any] = field(default_factory=dict)


class BrowserLauncher(ABC):
    """Abstract base class for all browser implementations."""

    _driver: Any = None

    def safe_get_address(self, url: str) -> None:
        """Navigate to the given URL using the internal driver, handling exceptions.

        Args:
            url: URL to navigate to
        """
        if self._driver is None:
            self.logger.error("No driver instance available for navigation.")
            return
        try:
            self._driver.get(url)
        except Exception as e:
            self.logger.error(f"Failed to navigate to {url}: {e}", exc_info=True)
            print("Caught exception!")
            print(f"Type       : {type(e).__name__}")
            print(f"Arguments  : {e.args}")

    def __init__(self, config: BrowserConfig, logger):
        """Initialize the browser launcher.
        Args:
            config: BrowserConfig instance with browser settings
            logger: Logger instance for logging operations
        """
        self.config = config
        self.logger = logger
        self._driver = None

    @abstractmethod
    def build_command_args(self, url: str) -> List[str]:
        """Build command-line arguments for launching the browser.

        Args:
            url: URL to open in the browser

        Returns:
            List of command-line arguments
        """
        pass

    @abstractmethod
    def launch(self, url: str) -> Any:
        """Launch the browser with the given URL and return the driver instance.

        Args:
            url: URL to open in the browser

        Returns:
            Popen process object representing the launched browser

        Raises:
            OSError: If the browser fails to launch
        """
        pass

    @property
    @abstractmethod
    def browser_name(self) -> str:
        """Return the browser name.

        Returns:
            Browser name (e.g., 'chrome', 'firefox', 'safari', 'edge')
        """
        pass
