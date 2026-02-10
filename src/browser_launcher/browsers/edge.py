"""Edge browser launcher implementation."""

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException
from .base import BrowserConfig, BrowserLauncher

class EdgeLauncher(BrowserLauncher):
    """Edge browser launcher implementation."""
    def build_command_args(self, url: str):
        return []  # Not used for WebDriver

    def launch(self, url: str) -> None:
        self.logger.debug(f"Launching Edge with url: {url}")
        try:
            edge_options = Options()
            if self.config.headless:
                edge_options.add_argument("--headless")
            if self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    edge_options.add_experimental_option(key, value)
            driver = webdriver.Edge(options=edge_options)
            self._driver = driver
            self.safe_get_address(url)
            self.logger.debug(f"Edge started and navigated to {url} with driver: {driver}")
        except WebDriverException as e:
            self.logger.error(f"Failed to launch Edge: {e}", exc_info=True)
            raise

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    @property
    def browser_name(self) -> str:
        return "edge"
