"""Authentication module for browser_launcher.

This module provides abstractions and base classes for implementing
authentication workflows with browsers.
"""

from .base import AuthenticatorBase
from .config import AuthConfig
from .dummy import DummyAuthenticator
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
from .retry import AuthRetryHandler

__all__ = [
    # Base classes
    "AuthenticatorBase",
    # Factory
    "AuthFactory",
    # Configuration
    "AuthConfig",
    # Result data
    "AuthResult",
    # Retry handler
    "AuthRetryHandler",
    # Dummy authenticator
    "DummyAuthenticator",
    # Exceptions
    "AuthError",
    "AuthConfigError",
    "AuthenticationFailedError",
    "AuthSessionError",
    "AuthTimeoutError",
    "CredentialsError",
]
