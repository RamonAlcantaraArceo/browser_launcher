"""Configuration management for browser launcher."""

from pathlib import Path
from typing import Any, Dict, Optional

import toml

from browser_launcher.auth.config import AuthConfig
from browser_launcher.browsers.base import BrowserConfig


class BrowserLauncherConfig:
    def get_cookie_rules(self, section: str):
        """Retrieve cookie rules for a given hierarchical section.

        Args:
            section: Hierarchical config section (e.g. users.{user}.{env}.{domain})

        Returns:
            List of cookie rule dicts or objects, or empty list if not found.
        """
        keys = section.split(".")
        data = self.config_data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return []
        return data.get("cookies", [])

    def get_console_logging(self) -> bool:
        """Return the console_logging setting from config,
        defaulting to False if not present."""
        return self.config_data.get("logging", {}).get("console_logging", False)

    def get_logging_level(self) -> str:
        return self.config_data.get("logging", {}).get("default_log_level", "WARNING")

    """Load and manage browser launcher configuration from TOML."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (
            Path.home() / ".browser_launcher" / "config.toml"
        )
        self.config_data = self._load_config()

    def _load_config(self):
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        return toml.load(self.config_path)

    def get_browser_config(
        self, browser_name: str, headless: bool = False
    ) -> BrowserConfig:
        browsers = self.config_data.get("browsers", {})
        browser_section = browsers.get(browser_name, {})
        binary_path = (
            Path(browser_section.get("binary_path"))
            if browser_section.get("binary_path")
            else None
        )
        user_data_dir = (
            Path(browser_section.get("user_data_dir"))
            if browser_section.get("user_data_dir")
            else None
        )
        custom_flags = browser_section.get("custom_flags")
        extra_options = browser_section.get("extra_options", {})
        return BrowserConfig(
            binary_path=binary_path,
            headless=headless or browser_section.get("headless", False),
            user_data_dir=user_data_dir,
            custom_flags=custom_flags,
            extra_options=extra_options,
        )

    def get_default_browser(self) -> str:
        return self.config_data.get("general", {}).get("default_browser", "chrome")

    def get_default_url(self) -> str:
        return self.config_data.get("urls", {}).get(
            "homepage", "https://www.microsoft.com"
        )

    def get_auth_config(
        self,
        module_name: Optional[str] = None,
        user: Optional[str] = None,
        env: Optional[str] = None,
    ) -> AuthConfig:
        """Get authentication configuration with hierarchical resolution.

        Resolution order (later values override earlier ones):
        1. Global auth defaults: [auth]
        2. Module-specific config: [auth.{module_name}]
        3. User/env auth config: [users.{user}.{env}.auth]
        4. Module config within user/env: [users.{user}.{env}.auth.{module_name}]

        Args:
            module_name: Name of the authentication module
            user: User identifier for hierarchical config
            env: Environment identifier for hierarchical config

        Returns:
            AuthConfig instance with merged configuration
        """
        # Start with empty config dict
        config_dict: Dict[str, Any] = {}

        # 1. Global auth defaults
        global_auth = self.config_data.get("auth", {})
        if isinstance(global_auth, dict):
            config_dict.update(global_auth)

        # 2. Module-specific global config
        if module_name and f"{module_name}" in global_auth:
            module_config = global_auth[module_name]
            if isinstance(module_config, dict):
                config_dict.update(module_config)

        # 3. User/env auth config
        if user and env:
            user_env_auth = self._get_nested_config(["users", user, env, "auth"])
            if user_env_auth:
                config_dict.update(user_env_auth)

                # 4. Module config within user/env
                if module_name and module_name in user_env_auth:
                    module_user_config = user_env_auth[module_name]
                    if isinstance(module_user_config, dict):
                        config_dict.update(module_user_config)

        # Convert nested dicts and filter valid AuthConfig fields
        return self._create_auth_config(config_dict)

    def get_auth_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get module-specific authentication configuration.

        Args:
            module_name: Name of the authentication module

        Returns:
            Dictionary of module-specific configuration
        """
        auth_config = self.config_data.get("auth", {})
        return auth_config.get(module_name, {})

    def get_available_auth_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured authentication modules.

        Returns:
            Dictionary mapping module names to their configurations
        """
        auth_config = self.config_data.get("auth", {})
        modules = {}

        for key, value in auth_config.items():
            # Skip top-level auth settings, only return module configs
            if isinstance(value, dict) and key not in [
                "timeout_seconds",
                "retry_attempts",
                "retry_delay_seconds",
                "headless",
                "credentials",
                "custom_options",
                "user_agent",
                "window_size",
                "page_load_timeout",
                "element_wait_timeout",
                "screenshot_on_failure",
                "screenshot_directory",
                "allowed_domains",
                "required_cookies",
            ]:
                modules[key] = value

        return modules

    def _get_nested_config(self, keys: list[str]) -> Optional[Dict[str, Any]]:
        """Get nested configuration value by traversing key path.

        Args:
            keys: List of keys to traverse (e.g., ["users", "alice", "prod", "auth"])

        Returns:
            Dictionary if found, None otherwise
        """
        data = self.config_data
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data if isinstance(data, dict) else None

    def _create_auth_config(self, config_dict: Dict[str, Any]) -> AuthConfig:
        """Create AuthConfig from dictionary, filtering invalid keys.

        Args:
            config_dict: Raw configuration dictionary

        Returns:
            AuthConfig instance
        """
        # Get valid AuthConfig field names
        from dataclasses import fields

        valid_fields = {f.name for f in fields(AuthConfig)}

        # Filter config dict to only include valid AuthConfig fields
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_fields}

        # Handle special field conversions
        if "screenshot_directory" in filtered_config:
            screenshot_dir = filtered_config["screenshot_directory"]
            if isinstance(screenshot_dir, str):
                filtered_config["screenshot_directory"] = Path(screenshot_dir)

        return AuthConfig(**filtered_config)
