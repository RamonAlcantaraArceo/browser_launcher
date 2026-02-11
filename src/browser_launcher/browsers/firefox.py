"""Firefox browser launcher implementation."""

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options

from .base import BrowserLauncher


class FirefoxLauncher(BrowserLauncher):
    """Firefox browser launcher implementation.

    Firefox uses different flag syntax than Chrome:
    - Uses single dash flags like -headless instead of --headless
    - Profile management with -profile flag instead of --user-data-dir
    - Limited experimental options compared to Chrome
    """

    def launch(self, url: str) -> None:
        """Launch Firefox with the given URL and set the driver instance internally."""
        self.logger.debug(f"Launching Firefox with url: {url}")
        try:
            firefox_options = Options()
            if self.config.headless:
                firefox_options.add_argument("-headless")
            if self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    setattr(firefox_options, key, value)
            driver = webdriver.Firefox(options=firefox_options)
            self._driver = driver
            self.safe_get_address(url)
            self.logger.debug(
                f"Firefox started and navigated to {url} with driver: {driver}"
            )
        except WebDriverException as e:
            self.logger.error(f"Failed to launch Firefox: {e}", exc_info=True)
            raise

    @property
    def driver(self) -> webdriver.Firefox:
        """Return the current Firefox driver instance, if any."""
        return self._driver

    @property
    def browser_name(self) -> str:
        """Return the browser name identifier."""
        return "firefox"
