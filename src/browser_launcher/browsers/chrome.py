"""Chrome browser implementation."""

import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from browser_launcher.browsers.base import BrowserLauncher


class ChromeLauncher(BrowserLauncher):
    """Chrome browser launcher implementation."""

    def launch(self, url: str) -> None:
        """Launch Chrome with the given URL and set the driver instance internally.

        Args:
            url: URL to open in Chrome

        Returns:
            Popen process object representing the launched browser

        Raises:
            OSError: If Chrome fails to launch
        """
        self.logger.debug(f"Launching Chrome with url: {url}")
        try:
            chrome_options = Options()

            # Enable headless mode if configured or running in CI
            is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
            should_use_headless = (self.config and self.config.headless) or is_ci

            if should_use_headless:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                self.logger.debug("Running Chrome in headless mode")

            # Add verbose logging for CI debugging
            service = None
            if is_ci:
                service = Service(log_output="chromedriver.log", verbose=True)
                self.logger.debug("Enabled ChromeDriver verbose logging for CI")

            if self.config and self.config.locale:
                chrome_options.add_experimental_option(
                    "prefs", {"intl.accept_languages": self.config.locale}
                )

            if self.config and self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    chrome_options.add_experimental_option(key, value)

            # Create ChromeDriver with service if configured
            if service:
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            self._driver = driver

            self.safe_get_address(url=url)

            self.logger.debug(
                f"Chrome started and navigated to {url} with driver: {driver}"
            )

        except WebDriverException as e:
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
