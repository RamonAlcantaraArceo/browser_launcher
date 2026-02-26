"""Edge browser launcher implementation."""

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.options import Options

from .base import BrowserLauncher


class EdgeLauncher(BrowserLauncher):
    """Edge browser launcher implementation."""

    def launch(self, url: str) -> None:
        self.logger.debug(f"Launching Edge with url: {url}")
        try:
            edge_options = Options()
            if self.config and self.config.headless:
                edge_options.add_argument("--headless")

            driver = webdriver.Edge(options=edge_options)
            self._driver = driver
            self.safe_get_address(url)
            self.logger.debug(
                f"Edge started and navigated to {url} with driver: {driver}"
            )
        except WebDriverException as e:
            self.logger.error(f"Failed to launch Edge: {e}", exc_info=True)
            raise

    @property
    def driver(self) -> webdriver.Edge:
        return self._driver

    @property
    def browser_name(self) -> str:
        return "edge"
