"""Dummy authenticator for testing and demonstration purposes.

This authenticator accepts any credentials and returns a test cookie with a
random value and short expiry time. It's designed to demonstrate the
authentication framework's logging and flow without requiring actual auth services.
"""

import logging
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .base import AuthenticatorBase
from .config import AuthConfig
from .result import AuthResult

logger = logging.getLogger(__name__)


class DummyAuthenticator(AuthenticatorBase):
    """Dummy authenticator that always succeeds with test cookies.

    This authenticator is useful for:
    - Testing the authentication framework
    - Demonstrating auth module implementation
    - Development when actual auth services are unavailable
    - Validating logging and error handling flows

    Any credentials are accepted, and a test cookie named 'DUMMY_SESSION'
    is returned with a random value and 5-minute expiry.
    """

    COOKIE_NAME = "DUMMY_SESSION"
    """Name of the test cookie returned by this authenticator."""

    COOKIE_EXPIRY_MINUTES = 5
    """Expiry time for test cookies in minutes."""

    def __init__(self, config: AuthConfig):
        """Initialize the dummy authenticator.

        Args:
            config: AuthConfig instance with authentication settings
        """
        logger.info("Initializing DummyAuthenticator")
        logger.debug(
            f"Config: timeout={config.timeout_seconds}s, "
            f"retry={config.retry_attempts}, headless={config.headless}"
        )
        super().__init__(config)
        logger.info("DummyAuthenticator initialized successfully")

    def authenticate(self, url: str, **kwargs) -> AuthResult:
        """Perform dummy authentication.

        Accepts any credentials and returns a test session cookie.

        Args:
            url: The URL to authenticate against (used for domain extraction)
            **kwargs: Additional parameters (ignored for dummy auth)

        Returns:
            AuthResult with a test session cookie

        Raises:
            CredentialsError: If username credential is missing
            AuthenticationFailedError: If simulated failure is requested
        """
        start_time = time.time()
        logger.info(f"Starting dummy authentication for URL: {url}")
        logger.debug(f"Additional kwargs: {list(kwargs.keys())}")

        # Extract domain from URL
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc or parsed_url.path
            logger.debug(f"Extracted domain: {domain}")
        except Exception as e:
            logger.error(f"Failed to parse URL '{url}': {e}", exc_info=True)
            domain = "example.com"
            logger.warning(f"Using fallback domain: {domain}")

        # Check for credentials (optional for dummy auth, but demonstrates validation)
        username = self.config.get_credential("username")
        logger.debug(f"Username from config: {username}")

        if not username:
            logger.warning("No username in credentials, using default 'test_user'")
            username = "test_user"

        # Check for simulated failure (for testing error paths)
        if self.config.get_credential("simulate_failure"):
            logger.warning("Simulated failure requested via credentials")
            duration = time.time() - start_time
            error_msg = "Simulated authentication failure for testing"
            logger.error(f"Authentication failed: {error_msg}")
            return AuthResult(
                success=False,
                error_message=error_msg,
                duration_seconds=duration,
                domain=domain,
                user=username,
            )

        # Generate random session token
        session_token = secrets.token_urlsafe(32)
        logger.debug(f"Generated session token: {session_token[:10]}...")

        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(minutes=self.COOKIE_EXPIRY_MINUTES)
        expiry_timestamp = int(expiry_time.timestamp())
        logger.debug(
            f"Cookie expiry: {expiry_time.isoformat()} "
            f"({self.COOKIE_EXPIRY_MINUTES} minutes from now)"
        )

        # Simulate authentication delay (configurable via custom_options)
        delay = self.config.custom_options.get("auth_delay_seconds", 0.5)
        if delay > 0:
            logger.debug(f"Simulating authentication delay: {delay}s")
            time.sleep(delay)

        # Create cookie dictionary matching Selenium's cookie format
        cookie = {
            "name": self.COOKIE_NAME,
            "value": session_token,
            "domain": domain,
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax",
            "expiry": expiry_timestamp,
        }

        logger.info(
            f"Authentication successful: created cookie '{self.COOKIE_NAME}' "
            f"for domain '{domain}'"
        )
        logger.debug(f"Cookie details: {cookie}")

        # Calculate duration
        duration = time.time() - start_time

        # Create and return result
        result = AuthResult(
            cookies=[cookie],
            success=True,
            timestamp=datetime.now(),
            domain=domain,
            user=username,
            session_data={
                "authenticator": self.__class__.__name__,
                "cookie_name": self.COOKIE_NAME,
                "expiry_minutes": self.COOKIE_EXPIRY_MINUTES,
                "auth_delay": delay,
            },
            duration_seconds=duration,
        )

        logger.info(
            f"Dummy authentication completed successfully in {duration:.2f}s "
            f"with {result.cookie_count} cookie(s)"
        )

        return result

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        """Validate configuration for dummy authenticator.

        Dummy auth accepts any valid AuthConfig - this method demonstrates
        custom validation that could be implemented by real authenticators.

        Args:
            config: AuthConfig to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        logger.debug(f"Validating configuration for {cls.__name__}")

        # Call parent validation first
        if not super().validate_config(config):
            logger.warning(f"Parent validation failed for {cls.__name__}")
            return False

        # Dummy-specific validation (demonstrations only)
        # Real authenticators might check for required credentials,
        # validate API endpoints, check custom_options, etc.

        auth_delay = config.custom_options.get("auth_delay_seconds", 0.5)
        if not isinstance(auth_delay, (int, float)) or auth_delay < 0:
            logger.warning(
                f"Invalid auth_delay_seconds in custom_options: {auth_delay}"
            )
            return False

        logger.debug(f"Configuration validated successfully for {cls.__name__}")
        return True

    def cleanup(self) -> None:
        """Clean up dummy authenticator resources.

        Demonstrates cleanup method - real authenticators might close
        API connections, clear temporary files, etc.
        """
        logger.debug(f"Cleaning up {self.__class__.__name__} resources")
        super().cleanup()
        logger.info(f"{self.__class__.__name__} cleanup completed")
