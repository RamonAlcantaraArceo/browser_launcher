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
        logger.debug(
            f"Initializing {self.__class__.__name__} with "
            f"timeout={config.timeout_seconds}s, retry={config.retry_attempts}, "
            f"headless={config.headless}"
        )
        self.config = config
        self._driver: Optional[WebDriver] = None
        logger.info(f"{self.__class__.__name__} initialized successfully")

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
        if driver is not None:
            logger.debug(
                f"Setting WebDriver instance for {self.__class__.__name__}: "
                f"{driver.__class__.__name__}"
            )
        else:
            logger.debug(f"Clearing WebDriver instance for {self.__class__.__name__}")
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
        logger.debug(f"Validating configuration for {cls.__name__}")

        try:
            # Basic validation - subclasses can override for specific validation
            if config.timeout_seconds <= 0:
                logger.warning(
                    f"Configuration validation failed for {cls.__name__}: "
                    f"Invalid timeout_seconds={config.timeout_seconds}"
                )
                return False
            if config.retry_attempts < 0:
                logger.warning(
                    f"Configuration validation failed for {cls.__name__}: "
                    f"Invalid retry_attempts={config.retry_attempts}"
                )
                return False

            logger.debug(f"Configuration validated successfully for {cls.__name__}")
            return True
        except Exception as e:
            logger.error(
                f"Error validating auth config for {cls.__name__}: {e}",
                exc_info=True,
            )
            return False

    def setup_driver(self, driver: WebDriver) -> None:
        """Set up the WebDriver for authentication.

        Configures timeouts and other driver settings based on the auth config.
        This method is optional and only needed for browser-based authentication.

        Args:
            driver: WebDriver instance to configure
        """
        logger.info(
            f"Setting up WebDriver for {self.__class__.__name__} authentication"
        )
        self._driver = driver

        if self._driver is not None:
            # Set timeouts based on auth config
            logger.debug(
                f"Configuring driver timeouts: "
                f"element_wait={self.config.element_wait_timeout}s, "
                f"page_load={self.config.page_load_timeout}s"
            )
            self._driver.implicitly_wait(self.config.element_wait_timeout)
            self._driver.set_page_load_timeout(self.config.page_load_timeout)

            # Set window size if driver supports it
            try:
                logger.debug(f"Setting window size to {self.config.window_size}")
                self._driver.set_window_size(*self.config.window_size)
                logger.debug("Window size set successfully")
            except Exception as e:
                logger.warning(f"Could not set window size: {e}", exc_info=True)

            logger.info("WebDriver setup completed successfully")

    def cleanup(self) -> None:
        """Clean up resources after authentication.

        This method can be overridden by subclasses to perform
        authentication-specific cleanup operations.
        For API-based authentication, this might involve clearing tokens or sessions.
        """
        logger.debug(f"Cleaning up {self.__class__.__name__} authentication resources")
        # Reset driver reference but don't quit it -
        # that's the responsibility of the browser launcher
        self._driver = None
        logger.debug("Authentication cleanup completed")

    def take_failure_screenshot(self, identifier: str = "auth_failed") -> Optional[str]:
        """Take a screenshot when authentication fails.

        Args:
            identifier: Unique identifier for the screenshot

        Returns:
            Path to the screenshot file if successful, None otherwise
        """
        if not self.config.screenshot_on_failure or not self._driver:
            logger.debug(
                "Screenshot not taken: feature disabled or no driver available"
            )
            return None

        if not self.config.screenshot_directory:
            logger.warning(
                "Screenshot directory not configured, cannot save screenshot"
            )
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
            logger.debug(f"Attempting to save screenshot to: {screenshot_path}")

            # Ensure directory exists
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)

            if self._driver.save_screenshot(str(screenshot_path)):
                logger.info(
                    f"Authentication failure screenshot saved: {screenshot_path}"
                )
                return str(screenshot_path)
            else:
                logger.warning("Failed to save authentication failure screenshot")
                return None

        except Exception as e:
            logger.error(
                f"Error taking authentication failure screenshot: {e}",
                exc_info=True,
            )
            return None
