"""Authentication factory for discovering and instantiating auth modules."""

import logging
from importlib.metadata import entry_points
from typing import Any, Dict, List, Optional, Type

from .base import AuthenticatorBase
from .config import AuthConfig
from .exceptions import AuthConfigError, AuthError

logger = logging.getLogger(__name__)


class AuthFactory:
    """Factory for discovering and creating authentication modules via entry points.

    This factory uses Python entry points to discover authentication modules
    dynamically, allowing external packages to register their own authenticators
    under the 'browser_launcher.authenticators' group.
    """

    _module_cache: Dict[str, Type[AuthenticatorBase]] = {}
    _discovery_cache: Optional[Dict[str, Type[AuthenticatorBase]]] = None

    @classmethod
    def discover_modules(
        cls, refresh_cache: bool = False
    ) -> Dict[str, Type[AuthenticatorBase]]:
        """Discover authentication modules via entry points.

        Searches for entry points under the 'browser_launcher.authenticators' group
        and validates that they implement the AuthenticatorBase interface.

        Args:
            refresh_cache: If True, force rediscovery of modules

        Returns:
            Dictionary mapping module names to authenticator classes

        Raises:
            AuthError: If module discovery or validation fails
        """
        if cls._discovery_cache is not None and not refresh_cache:
            return cls._discovery_cache.copy()

        discovered = {}

        try:
            # Discover entry points for authentication modules
            auth_entry_points = entry_points(group="browser_launcher.authenticators")

            for entry_point in auth_entry_points:
                module_name = entry_point.name

                try:
                    logger.debug(f"Loading authentication module: {module_name}")
                    authenticator_class = entry_point.load()

                    # Validate that the class implements AuthenticatorBase
                    if not issubclass(authenticator_class, AuthenticatorBase):
                        logger.warning(
                            f"Module '{module_name}' does not implement "
                            f"AuthenticatorBase, skipping"
                        )
                        continue

                    # Validate that it's not the abstract base class itself
                    if authenticator_class is AuthenticatorBase:
                        logger.warning(
                            f"Module '{module_name}' is the abstract base class, "
                            f"skipping"
                        )
                        continue

                    discovered[module_name] = authenticator_class
                    logger.info(f"Discovered authentication module: {module_name}")

                except Exception as e:
                    logger.error(
                        f"Failed to load authentication module '{module_name}': {e}"
                    )
                    continue

            # Cache the discovery results
            cls._discovery_cache = discovered
            logger.info(f"Discovered {len(discovered)} authentication modules")

        except Exception as e:
            logger.error(f"Error during authentication module discovery: {e}")
            raise AuthError(f"Failed to discover authentication modules: {e}") from e

        return discovered.copy()

    @classmethod
    def get_available_modules(cls) -> List[str]:
        """Get list of available authentication module names.

        Returns:
            List of discovered module names
        """
        modules = cls.discover_modules()
        return list(modules.keys())

    @classmethod
    def create(
        cls, module_name: str, config: AuthConfig, validate_config: bool = True
    ) -> AuthenticatorBase:
        """Create an authentication module instance.

        Args:
            module_name: Name of the authentication module to create
            config: AuthConfig instance for the authenticator
            validate_config: Whether to validate config before creation

        Returns:
            Instantiated authenticator instance

        Raises:
            AuthConfigError: If module is not found or config is invalid
            AuthError: If module creation fails
        """
        # Check cache first
        if module_name in cls._module_cache:
            authenticator_class = cls._module_cache[module_name]
        else:
            # Discover modules if not in cache
            available_modules = cls.discover_modules()

            if module_name not in available_modules:
                available = ", ".join(available_modules.keys())
                raise AuthConfigError(
                    f"Authentication module '{module_name}' not found",
                    f"Available modules: {available}",
                )

            authenticator_class = available_modules[module_name]
            cls._module_cache[module_name] = authenticator_class

        # Validate configuration if requested
        if validate_config:
            if not cls.validate_module_config(authenticator_class, config):
                raise AuthConfigError(
                    f"Invalid configuration for module '{module_name}'",
                    "Configuration validation failed",
                )

        try:
            logger.debug(f"Creating authentication module instance: {module_name}")
            authenticator = authenticator_class(config)
            logger.info(f"Created authentication module: {module_name}")
            return authenticator

        except Exception as e:
            logger.error(f"Failed to create authentication module '{module_name}': {e}")
            raise AuthError(
                f"Failed to create authentication module '{module_name}': {e}"
            ) from e

    @classmethod
    def validate_module_config(
        cls, authenticator_class: Type[AuthenticatorBase], config: AuthConfig
    ) -> bool:
        """Validate configuration for a specific authentication module.

        Checks if the authenticator class has a custom validate_config class method,
        and falls back to basic validation if not.

        Args:
            authenticator_class: The authenticator class to validate config for
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Check if the authenticator class has custom validation
            if hasattr(authenticator_class, "validate_config"):
                return authenticator_class.validate_config(config)

            # Fall back to basic AuthConfig validation
            if config.timeout_seconds <= 0:
                logger.error("Invalid timeout_seconds in auth config")
                return False

            if config.retry_attempts < 0:
                logger.error("Invalid retry_attempts in auth config")
                return False

            return True

        except Exception as e:
            logger.error(
                f"Error validating config for {authenticator_class.__name__}: {e}"
            )
            return False

    @classmethod
    def get_module_info(cls, module_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific authentication module.

        Args:
            module_name: Name of the module to get info for

        Returns:
            Dictionary with module information or None if not found
        """
        available_modules = cls.discover_modules()

        if module_name not in available_modules:
            return None

        authenticator_class = available_modules[module_name]

        info = {
            "name": module_name,
            "class": authenticator_class.__name__,
            "module": authenticator_class.__module__,
            "docstring": authenticator_class.__doc__,
            "has_custom_validation": hasattr(authenticator_class, "validate_config"),
        }

        return info

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached modules and discovery results.

        Useful for testing or when modules are added/removed dynamically.
        """
        cls._module_cache.clear()
        cls._discovery_cache = None
        logger.debug("Cleared authentication module cache")

    @classmethod
    def is_module_available(cls, module_name: str) -> bool:
        """Check if a specific authentication module is available.

        Args:
            module_name: Name of the module to check

        Returns:
            True if module is available, False otherwise
        """
        try:
            available_modules = cls.discover_modules()
            return module_name in available_modules
        except Exception:
            return False
