"""Authentication result dataclass."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AuthResult:
    """Result data from an authentication process.

    Contains cookie data and metadata returned from successful authentication.
    """

    cookies: List[Dict[str, Any]] = field(default_factory=list)
    """List of cookie dictionaries with name, value, domain, path, etc."""

    success: bool = True
    """Whether authentication was successful."""

    timestamp: datetime = field(default_factory=datetime.now)
    """When the authentication was performed."""

    domain: Optional[str] = None
    """The domain that was authenticated against."""

    user: Optional[str] = None
    """The user identifier used for authentication."""

    environment: Optional[str] = None
    """The environment context (e.g., 'staging', 'production')."""

    session_data: Dict[str, Any] = field(default_factory=dict)
    """Additional session metadata from authentication."""

    error_message: Optional[str] = None
    """Error message if authentication failed."""

    duration_seconds: Optional[float] = None
    """How long authentication took in seconds."""

    def __post_init__(self):
        """Validate AuthResult after initialization."""
        if not self.success and not self.error_message:
            self.error_message = "Authentication failed with no specific error message"
        elif self.success and self.error_message:
            # Clear error message if marked as successful
            self.error_message = None

    @property
    def cookie_count(self) -> int:
        """Return the number of cookies in the result."""
        return len(self.cookies)

    def get_cookie_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific cookie by name.

        Args:
            name: The cookie name to search for

        Returns:
            Cookie dictionary if found, None otherwise
        """
        for cookie in self.cookies:
            if cookie.get("name") == name:
                return cookie
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert AuthResult to dictionary format.

        Returns:
            Dictionary representation of the AuthResult
        """
        return {
            "cookies": self.cookies,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "domain": self.domain,
            "user": self.user,
            "environment": self.environment,
            "session_data": self.session_data,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
            "cookie_count": self.cookie_count,
        }
