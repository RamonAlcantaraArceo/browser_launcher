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
            logger.debug("Using cached authentication module discovery results")
            return cls._discovery_cache.copy()

        logger.info("Starting authentication module discovery")
        discovered = {}

        try:
            # Discover entry points for authentication modules
            auth_entry_points = entry_points(group="browser_launcher.authenticators")
            logger.debug(
                f"Found {len(list(auth_entry_points))} entry points in "
                f"'browser_launcher.authenticators' group"
            )

            for entry_point in auth_entry_points:
                module_name = entry_point.name

                try:
                    logger.debug(f"Loading authentication module: {module_name}")
                    authenticator_class = entry_point.load()
                    logger.debug(
                        f"Loaded class {authenticator_class.__name__} from "
                        f"{authenticator_class.__module__}"
                    )

                    # Validate that the class implements AuthenticatorBase
                    if not issubclass(authenticator_class, AuthenticatorBase):
                        logger.warning(
                            f"Module '{module_name}' does not implement "
                            f"AuthenticatorBase (got {authenticator_class.__name__}), "
                            f"skipping"
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
                    logger.info(
                        f"Discovered authentication module: {module_name} "
                        f"({authenticator_class.__name__})"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to load authentication module '{module_name}': {e}",
                        exc_info=True,
                    )
                    logger.debug(
                        f"Module load failure details - entry_point: {entry_point}, "
                        f"error type: {type(e).__name__}"
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
        logger.debug(
            f"Creating authentication module '{module_name}' with config: "
            f"timeout={config.timeout_seconds}s, retry={config.retry_attempts}, "
            f"headless={config.headless}"
        )

        # Check cache first
        if module_name in cls._module_cache:
            logger.debug(f"Using cached authenticator class for '{module_name}'")
            authenticator_class = cls._module_cache[module_name]
        else:
            # Discover modules if not in cache
            logger.debug(f"Discovering modules to find '{module_name}'")
            available_modules = cls.discover_modules()

            if module_name not in available_modules:
                available = ", ".join(available_modules.keys())
                logger.error(
                    f"Authentication module '{module_name}' not found. "
                    f"Available: {available}"
                )
                raise AuthConfigError(
                    f"Authentication module '{module_name}' not found",
                    f"Available modules: {available}",
                )

            authenticator_class = available_modules[module_name]
            cls._module_cache[module_name] = authenticator_class
            logger.debug(f"Cached authenticator class '{module_name}'")

        # Validate configuration if requested
        if validate_config:
            logger.debug(f"Validating configuration for module '{module_name}'")
            if not cls.validate_module_config(authenticator_class, config):
                logger.warning(
                    f"Configuration validation failed for module '{module_name}'"
                )
                raise AuthConfigError(
                    f"Invalid configuration for module '{module_name}'",
                    "Configuration validation failed",
                )
            logger.debug(f"Configuration validated successfully for '{module_name}'")

        try:
            logger.debug(f"Creating authentication module instance: {module_name}")
            authenticator = authenticator_class(config)
            logger.info(
                f"Created authentication module: {module_name} "
                f"({authenticator_class.__name__})"
            )
            return authenticator

        except Exception as e:
            logger.error(
                f"Failed to create authentication module '{module_name}': {e}",
                exc_info=True,
            )
            logger.debug(
                f"Module creation failure details - class: {authenticator_class}, "
                f"error type: {type(e).__name__}"
            )
            raise AuthError(
                f"Failed to create authentication module '{module_name}': {e}"
            ) from e

    @classmethod
    def validate_module_config(
        cls, authenticator_class: Type[AuthenticatorBase], config: AuthConfig
    ) -> bool:
        """Validate configuration for a specific authentication module.

        Calls the authenticator class's validate_config method, which is defined
        in AuthenticatorBase and can be overridden by subclasses for custom validation.

        Args:
            authenticator_class: The authenticator class to validate config for
            config: Configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        logger.debug(
            f"Validating config for {authenticator_class.__name__}: "
            f"timeout={config.timeout_seconds}s, retry={config.retry_attempts}"
        )

        try:
            # Call validate_config, which may be overridden by subclasses
            if "validate_config" in authenticator_class.__dict__:
                logger.debug(
                    f"{authenticator_class.__name__} has custom validate_config method"
                )
            else:
                logger.debug(
                    "Using base validate_config method for"
                    f" {authenticator_class.__name__}"
                )

            result = authenticator_class.validate_config(config)
            if result:
                logger.debug(
                    f"Config validation passed for {authenticator_class.__name__}"
                )
            else:
                logger.warning(
                    f"Config validation failed for {authenticator_class.__name__}"
                )
            return result

        except Exception as e:
            logger.error(
                f"Error validating config for {authenticator_class.__name__}: {e}",
                exc_info=True,
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

        base_validate = AuthenticatorBase.validate_config
        auth_validate = getattr(authenticator_class, "validate_config", None)
        has_custom_validation = (
            auth_validate is not None and auth_validate is not base_validate
        )

        info = {
            "name": module_name,
            "class": authenticator_class.__name__,
            "module": authenticator_class.__module__,
            "docstring": authenticator_class.__doc__,
            "has_custom_validation": has_custom_validation,
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
