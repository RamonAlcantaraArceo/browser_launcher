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

    def __init__(self, config: BrowserConfig, logger):
        """Initialize the browser launcher.

        Args:
            config: BrowserConfig instance with browser settings
            logger: Logger instance for logging operations
        """
        self.config = config
        self.logger = logger

    @abstractmethod
    def validate_binary(self) -> bool:
        """Check if browser binary exists and is executable.

        Returns:
            True if binary exists and is executable, False otherwise
        """
        pass

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
    def launch(self, url: str) -> subprocess.Popen:
        """Launch the browser with the given URL.

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
