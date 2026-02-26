"""Chrome browser implementation."""

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options

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
            if self.config and self.config.headless:
                chrome_options.add_argument("--headless")

            if self.config and self.config.locale:
                chrome_options.add_experimental_option("prefs", {"intl.accept_languages": self.config.locale})

            if self.config and self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    chrome_options.add_experimental_option(key, value)
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
