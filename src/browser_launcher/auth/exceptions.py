"""Authentication exceptions hierarchy."""

from typing import Optional


class AuthError(Exception):
    """Base exception for authentication-related errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        """Initialize AuthError.

        Args:
            message: Human-readable error message
            details: Optional additional error details
        """
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class AuthenticationFailedError(AuthError):
    """Raised when authentication process fails."""

    pass


class AuthConfigError(AuthError):
    """Raised when authentication configuration is invalid."""

    pass


class AuthTimeoutError(AuthError):
    """Raised when authentication process times out."""

    pass


class CredentialsError(AuthError):
    """Raised when credentials are missing or invalid."""

    pass


class AuthSessionError(AuthError):
    """Raised when there are issues with the authentication session."""

    pass
