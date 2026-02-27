"""Authentication base class and abstractions."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from .config import AuthConfig
from .result import AuthResult

logger = logging.getLogger(__name__)


class AuthenticatorBase(ABC):
    """Abstract base class for all authentication implementations.

    Provides the common interface and functionality that all authenticators
    must implement. Each authentication method (SSO, form-based, API, etc.)
    should inherit from this class.
    """

    def __init__(self, config: AuthConfig):
        """Initialize the authenticator.

        Args:
            config: AuthConfig instance with authentication settings
        """
        self.config = config
        self._driver: Optional[WebDriver] = None

    @property
    def driver(self) -> Optional[WebDriver]:
        """Get the current WebDriver instance.

        Returns:
            WebDriver instance if available, None otherwise
        """
        return self._driver

    @driver.setter
    def driver(self, driver: Optional[WebDriver]) -> None:
        """Set the WebDriver instance.

        Args:
            driver: WebDriver instance to use for authentication
        """
        self._driver = driver

    @abstractmethod
    def authenticate(self, url: str, **kwargs) -> AuthResult:
        """Perform authentication against the specified URL or endpoint.

        This method must be implemented by all concrete authenticator classes.
        It should handle the complete authentication flow and return the
        results including any cookies obtained.

        For browser-based authentication, this would navigate to the URL
        and interact with the page.
        For API-based authentication, this would make HTTP requests to the endpoint.

        Args:
            url: The URL or API endpoint to authenticate against
            **kwargs: Additional authentication parameters specific to the
                implementation

        Returns:
            AuthResult containing authentication results and cookie data

        Raises:
            AuthenticationFailedError: When authentication fails
            AuthTimeoutError: When authentication times out
            AuthConfigError: When configuration is invalid
            CredentialsError: When credentials are missing or invalid
        """
        pass

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        """Validate authentication configuration.

        Args:
            config: AuthConfig to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Basic validation - subclasses can override for specific validation
            if config.timeout_seconds <= 0:
                logger.error("Invalid timeout_seconds in auth config")
                return False
            if config.retry_attempts < 0:
                logger.error("Invalid retry_attempts in auth config")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating auth config: {e}")
            return False

    def setup_driver(self, driver: WebDriver) -> None:
        """Set up the WebDriver for authentication.

        Configures timeouts and other driver settings based on the auth config.
        This method is optional and only needed for browser-based authentication.

        Args:
            driver: WebDriver instance to configure
        """
        self._driver = driver

        if self._driver is not None:
            # Set timeouts based on auth config
            self._driver.implicitly_wait(self.config.element_wait_timeout)
            self._driver.set_page_load_timeout(self.config.page_load_timeout)

            # Set window size if driver supports it
            try:
                self._driver.set_window_size(*self.config.window_size)
            except Exception as e:
                logger.warning(f"Could not set window size: {e}")

    def cleanup(self) -> None:
        """Clean up resources after authentication.

        This method can be overridden by subclasses to perform
        authentication-specific cleanup operations.
        For API-based authentication, this might involve clearing tokens or sessions.
        """
        # Reset driver reference but don't quit it -
        # that's the responsibility of the browser launcher
        self._driver = None

    def take_failure_screenshot(self, identifier: str = "auth_failed") -> Optional[str]:
        """Take a screenshot when authentication fails.

        Args:
            identifier: Unique identifier for the screenshot

        Returns:
            Path to the screenshot file if successful, None otherwise
        """
        if not self.config.screenshot_on_failure or not self._driver:
            return None

        if not self.config.screenshot_directory:
            logger.warning("Screenshot directory not configured")
            return None

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{identifier}_{timestamp}.png"

            # Ensure screenshot_directory is a Path object
            if isinstance(self.config.screenshot_directory, str):
                screenshot_dir = Path(self.config.screenshot_directory)
            else:
                screenshot_dir = self.config.screenshot_directory

            screenshot_path = screenshot_dir / filename

            # Ensure directory exists
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            if self._driver.save_screenshot(str(screenshot_path)):
                logger.info(f"Screenshot saved: {screenshot_path}")
                return str(screenshot_path)
            else:
                logger.warning("Failed to save screenshot")
                return None

        except Exception as e:
            logger.error(f"Error taking failure screenshot: {e}")
            return None
