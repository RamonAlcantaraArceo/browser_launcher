"""Authentication module for browser_launcher.

This module provides abstractions and base classes for implementing
authentication workflows with browsers.
"""

from .base import AuthenticatorBase
from .config import AuthConfig
from .exceptions import (
    AuthConfigError,
    AuthenticationFailedError,
    AuthError,
    AuthSessionError,
    AuthTimeoutError,
    CredentialsError,
)
from .factory import AuthFactory
from .result import AuthResult

__all__ = [
    # Base classes
    "AuthenticatorBase",
    # Factory
    "AuthFactory",
    # Configuration
    "AuthConfig",
    # Result data
    "AuthResult",
    # Exceptions
    "AuthError",
    "AuthConfigError",
    "AuthenticationFailedError",
    "AuthSessionError",
    "AuthTimeoutError",
    "CredentialsError",
]
