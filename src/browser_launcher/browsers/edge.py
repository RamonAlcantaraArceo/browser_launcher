"""Edge browser launcher implementation."""

import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

from .base import BrowserLauncher


class EdgeLauncher(BrowserLauncher):
    """Edge browser launcher implementation."""

    def launch(self, url: str) -> None:
        self.logger.debug(f"Launching Edge with url: {url}")
        try:
            edge_options = Options()

            # Enable headless mode if configured or running in CI
            is_ci = os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"
            should_use_headless = (self.config and self.config.headless) or is_ci

            if should_use_headless:
                edge_options.add_argument("--headless")
                edge_options.add_argument("--no-sandbox")
                edge_options.add_argument("--disable-dev-shm-usage")
                self.logger.debug("Running Edge in headless mode")

            # Add verbose logging for CI debugging
            service = None
            if is_ci:
                service = Service(log_output="edgedriver.log", verbose=True)
                self.logger.debug("Enabled EdgeDriver verbose logging for CI")

            if self.config and self.config.locale:
                edge_options.add_experimental_option(
                    "prefs", {"intl.accept_languages": self.config.locale}
                )

            if self.config and self.config.extra_options:
                for key, value in self.config.extra_options.items():
                    edge_options.add_experimental_option(key, value)

            # Create EdgeDriver with service if configured
            if service:
                driver = webdriver.Edge(service=service, options=edge_options)
            else:
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
