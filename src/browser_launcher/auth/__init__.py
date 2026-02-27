"""Authentication module for browser_launcher.

This module provides abstractions and base classes for implementing
authentication workflows with browsers.
"""

from .base import AuthenticatorBase
from .config import AuthConfig
from .exceptions import (
    AuthError,
    AuthConfigError,
    AuthenticationFailedError,
    AuthSessionError,
    AuthTimeoutError,
    CredentialsError,
)
from .result import AuthResult

__all__ = [
    # Base classes
    "AuthenticatorBase",
    
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