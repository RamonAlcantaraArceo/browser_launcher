"""Chrome browser implementation."""

from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from browser_launcher.browsers.base import BrowserLauncher


class ChromeLauncher(BrowserLauncher):
    """Chrome browser launcher implementation."""

    # Default flags for Chrome automation
    _DEFAULT_FLAGS = [
        "--disable-sync",
        "--disable-default-apps",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    def build_command_args(self, url: str) -> List[str]:
        """Build Chrome command-line arguments.

        Args:
            url: URL to open in Chrome

        Returns:
            List of command-line arguments
        """
        args = [str(self.config.binary_path)]

        # Add default flags
        args.extend(self._DEFAULT_FLAGS)

        # Add headless flag if requested
        if self.config.headless:
            args.append("--headless")

        # Add user data directory if specified
        if self.config.user_data_dir:
            args.append(f"--user-data-dir={self.config.user_data_dir}")

        # Add custom flags if provided
        if self.config.custom_flags:
            args.extend(self.config.custom_flags)

        # Add URL as last argument
        args.append(url)

        return args

    def launch(self, url: str) -> None:
        """Launch Chrome with the given URL and set the driver instance internally.

        Args:
            url: URL to open in Chrome

        Returns:
            Popen process object representing the launched browser

        Raises:
            OSError: If Chrome fails to launch
        """
        # args = self.build_command_args(url)
        self.logger.debug(f"Launching Chrome with url: {url}")
        try:
            chrome_options = Options()
            if self.config and self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    chrome_options.add_experimental_option(key, value)
            driver = webdriver.Chrome(options=chrome_options)
            self._driver = driver

            self.safe_get_address(url=url)

            self.logger.debug(
                f"Chrome started and navigated to {url} with driver: {driver}"
            )

        except Exception as e:
            self.logger.error(f"Failed to launch Chrome: {e}", exc_info=True)
            raise

    @property
    def driver(self) -> webdriver.Chrome:
        """Return the current Chrome driver instance, if any."""
        return self._driver

    @property
    def browser_name(self) -> str:
        """Return the browser name.

        Returns:
            'chrome'
        """
        return "chrome"
