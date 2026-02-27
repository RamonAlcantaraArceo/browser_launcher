"""Authentication configuration dataclass."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuthConfig:
    """Configuration for authentication processes.

    Contains settings for authentication timeouts, credentials,
    and authentication-specific browser options.
    """

    timeout_seconds: int = 30
    """Maximum time to wait for authentication to complete."""

    retry_attempts: int = 1
    """Number of retry attempts on authentication failure."""

    retry_delay_seconds: float = 1.0
    """Delay between retry attempts in seconds."""

    headless: bool = True
    """Whether to run authentication in headless mode."""

    credentials: Dict[str, Any] = field(default_factory=dict)
    """Authentication credentials and settings."""

    custom_options: Dict[str, Any] = field(default_factory=dict)
    """Browser-specific options for authentication."""

    user_agent: Optional[str] = None
    """Custom user agent string for authentication."""

    window_size: tuple[int, int] = (1920, 1080)
    """Browser window size for authentication (width, height)."""

    page_load_timeout: int = 20
    """Maximum time to wait for page loads during authentication."""

    element_wait_timeout: int = 10
    """Maximum time to wait for page elements during authentication."""

    screenshot_on_failure: bool = False
    """Whether to take screenshots when authentication fails."""

    screenshot_directory: Optional[Path] = None
    """Directory to save failure screenshots."""

    allowed_domains: List[str] = field(default_factory=list)
    """List of domains allowed for authentication."""

    required_cookies: List[str] = field(default_factory=list)
    """List of cookie names that must be present after authentication."""

    def __post_init__(self):
        """Validate AuthConfig after initialization."""
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")

        if self.page_load_timeout <= 0:
            raise ValueError("page_load_timeout must be positive")

        if self.element_wait_timeout <= 0:
            raise ValueError("element_wait_timeout must be positive")

        if len(self.window_size) != 2 or any(dim <= 0 for dim in self.window_size):
            raise ValueError("window_size must be a tuple of two positive integers")

        # Convert screenshot_directory to Path if it's a string
        if isinstance(self.screenshot_directory, str):
            self.screenshot_directory = Path(self.screenshot_directory)

    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get a credential value by key.

        Args:
            key: The credential key to retrieve
            default: Default value if key is not found

        Returns:
            Credential value or default
        """
        return self.credentials.get(key, default)

    def set_credential(self, key: str, value: Any) -> None:
        """Set a credential value.

        Args:
            key: The credential key to set
            value: The credential value
        """
        self.credentials[key] = value

    def validate_required_cookies(self, cookie_names: List[str]) -> bool:
        """Check if all required cookies are present in the given list.

        Args:
            cookie_names: List of cookie names to check

        Returns:
            True if all required cookies are present, False otherwise
        """
        if not self.required_cookies:
            return True
        return all(name in cookie_names for name in self.required_cookies)

    def to_dict(self) -> Dict[str, Any]:
        """Convert AuthConfig to dictionary format.

        Returns:
            Dictionary representation of the AuthConfig
        """
        return {
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "headless": self.headless,
            "credentials": self.credentials.copy(),
            "custom_options": self.custom_options.copy(),
            "user_agent": self.user_agent,
            "window_size": self.window_size,
            "page_load_timeout": self.page_load_timeout,
            "element_wait_timeout": self.element_wait_timeout,
            "screenshot_on_failure": self.screenshot_on_failure,
            "screenshot_directory": str(self.screenshot_directory) if self.screenshot_directory else None,
            "allowed_domains": self.allowed_domains.copy(),
            "required_cookies": self.required_cookies.copy(),
        }