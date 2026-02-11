"""Safari browser launcher implementation."""

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.safari.options import Options

from .base import BrowserLauncher


class SafariLauncher(BrowserLauncher):
    """Safari browser launcher implementation."""

    def build_command_args(self, url: str):
        return []  # Not used for WebDriver

    def launch(self, url: str) -> None:
        self.logger.debug(f"Launching Safari with url: {url}")
        try:
            safari_options = Options()
            if self.config.headless:
                self.logger.warning(
                    "Safari does not support headless mode. Ignoring headless flag."
                )
            # Safari WebDriver does not support extra_options or custom flags
            driver = webdriver.Safari(options=safari_options)
            self._driver = driver
            self.safe_get_address(url)
            self.logger.debug(
                f"Safari started and navigated to {url} with driver: {driver}"
            )
        except WebDriverException as e:
            self.logger.error(f"Failed to launch Safari: {e}", exc_info=True)
            raise

    @property
    def driver(self) -> webdriver.Safari:
        return self._driver

    @property
    def browser_name(self) -> str:
        return "safari"
