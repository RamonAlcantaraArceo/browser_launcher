"""
Cookie management module for browser_launcher.

Provides dataclasses and configuration loader for hierarchical, user/env/domain-aware
cookie rules and cache.
All docstrings use Google-style format.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CookieRule:
    """Represents a rule for a cookie for a specific domain.

    Attributes:
        domain (str): The domain this cookie applies to.
        name (str): The canonical cookie name.
        variants (Optional[Dict[str, str]]): Browser-specific cookie name variants.
        ttl_seconds (Optional[int]): Time-to-live override for this cookie, in seconds.
    """

    domain: str
    name: str
    variants: Optional[Dict[str, str]] = field(default_factory=dict)
    ttl_seconds: Optional[int] = None


@dataclass
class CacheEntry:
    """Represents a cached cookie value with timestamp and TTL.

    Attributes:
        value (str): The cookie value.
        timestamp (datetime): When the cookie was last set or persisted.
        ttl_seconds (int): Time-to-live for this cookie, in seconds (default 8 hours).
    """

    value: str
    timestamp: datetime
    ttl_seconds: int = 28800  # Default 8 hours

    def is_valid(self, now: Optional[datetime] = None) -> bool:
        """Check if the cache entry is still valid based on TTL.

        Args:
            now (Optional[datetime]): The current time. If None, uses UTC now.

        Returns:
            bool: True if the entry is valid, False if expired.
        """
        now = now or datetime.now(timezone.utc)
        return (now - self.timestamp).total_seconds() < self.ttl_seconds


class CookieConfig:
    """Loads and queries hierarchical cookie configuration for users, environments,
    and domains.

    Args:
        config_data (Dict[str, Any]): Parsed configuration data (from TOML or similar).
    """

    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data

    def get_rules(self, user: str, env: str, domain: str) -> List[CookieRule]:
        """Get all cookie rules for a given user, environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            List[CookieRule]: List of cookie rules for this context.
        """
        section = (
            self.config_data.get("users", {}).get(user, {}).get(env, {}).get(domain, {})
        )
        rules = []
        for cookie in section.get("cookies", []):
            rules.append(
                CookieRule(
                    domain=domain,
                    name=cookie.get("name"),
                    variants=cookie.get("variants", {}),
                    ttl_seconds=section.get("ttl_seconds", 28800),
                )
            )
        return rules

    def get_cache_entries(self, user: str, env: str, domain: str) -> List[CacheEntry]:
        """Get all cached cookie entries for a given user, environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            List[CacheEntry]: List of cache entries for this context.
        """
        section = (
            self.config_data.get("users", {}).get(user, {}).get(env, {}).get(domain, {})
        )
        entries = []
        for cookie in section.get("cookies", []):
            if "value" in cookie and "timestamp" in cookie:
                ts = datetime.fromisoformat(cookie["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entries.append(
                    CacheEntry(
                        value=cookie["value"],
                        timestamp=ts,
                        ttl_seconds=section.get("ttl_seconds", 28800),
                    )
                )
        return entries

    def load_cookie_cache(
        self, user: str, env: str, domain: str
    ) -> Dict[str, CacheEntry]:
        """Load the cookie cache for a given user, environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            Dict[str, CacheEntry]: Mapping of cookie name to cache entry.
        """
        section = (
            self.config_data.get("users", {}).get(user, {}).get(env, {}).get(domain, {})
        )
        cache: Dict[str, CacheEntry] = {}
        for cookie in section.get("cookies", []):
            if "name" in cookie and "value" in cookie and "timestamp" in cookie:
                ts = datetime.fromisoformat(cookie["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                cache[cookie["name"]] = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=section.get("ttl_seconds", 28800),
                )
        return cache

    def save_cookie_cache(
        self, user: str, env: str, domain: str, cache: Dict[str, CacheEntry]
    ) -> None:
        """Save the cookie cache for a given user, environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.
            cache (Dict[str, CacheEntry]): Mapping of cookie name to cache entry.

        Returns:
            None
        """
        section = (
            self.config_data.setdefault("users", {})
            .setdefault(user, {})
            .setdefault(env, {})
            .setdefault(domain, {})
        )
        cookies_list = []
        for name, entry in cache.items():
            cookies_list.append(
                {
                    "name": name,
                    "value": entry.value,
                    "timestamp": entry.timestamp.isoformat(),
                }
            )
        section["cookies"] = cookies_list

    def update_cookie_cache(
        self,
        user: str,
        env: str,
        domain: str,
        name: str,
        value: str,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Update a single cookie cache entry for a given user, environment,
        domain, and cookie name.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.
            name (str): The cookie name.
            value (str): The cookie value.
            ttl_seconds (Optional[int]): Optional TTL override in seconds.

        Returns:
            None
        """
        section = (
            self.config_data.setdefault("users", {})
            .setdefault(user, {})
            .setdefault(env, {})
            .setdefault(domain, {})
        )
        cookies = section.setdefault("cookies", [])
        now = datetime.now(timezone.utc)
        # Find existing cookie
        found = False
        for cookie in cookies:
            if cookie.get("name") == name:
                cookie["value"] = value
                cookie["timestamp"] = now.isoformat()
                found = True
                break
        if not found:
            cookies.append(
                {
                    "name": name,
                    "value": value,
                    "timestamp": now.isoformat(),
                }
            )
        if ttl_seconds is not None:
            section["ttl_seconds"] = ttl_seconds

    def clear_cookie_cache(self, user: str, env: str, domain: str) -> None:
        """Clear all cookie cache entries for a given user, environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            None
        """
        section = (
            self.config_data.setdefault("users", {})
            .setdefault(user, {})
            .setdefault(env, {})
            .setdefault(domain, {})
        )
        section["cookies"] = []

    def get_valid_cookie_cache(
        self, user: str, env: str, domain: str
    ) -> Dict[str, CacheEntry]:
        """Get only valid (non-expired) cookie cache entries for a given user,
        environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            Dict[str, CacheEntry]: Mapping of cookie name to valid cache entry.
        """
        cache = self.load_cookie_cache(user, env, domain)
        now = datetime.now(timezone.utc)
        valid_cache = {}
        for name, entry in cache.items():
            if entry.is_valid(now=now):
                valid_cache[name] = entry
        return valid_cache

    def load_cookie_cache_from_config(
        self, user: str, env: str, domain: str
    ) -> Dict[str, CacheEntry]:
        """Parse persisted cookies from config for a given user, environment,
        and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            Dict[str, CacheEntry]: Mapping of cookie name to cache entry.
        """
        section = (
            self.config_data.get("users", {}).get(user, {}).get(env, {}).get(domain, {})
        )
        ttl = section.get("ttl_seconds", 28800)
        cache: Dict[str, CacheEntry] = {}
        for cookie in section.get("cookies", []):
            if "name" in cookie and "value" in cookie and "timestamp" in cookie:
                ts = datetime.fromisoformat(cookie["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                cache[cookie["name"]] = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=ttl,
                )
        return cache

    def save_cookies_to_cache(
        self, user: str, env: str, domain: str, cookies: Dict[str, CacheEntry]
    ) -> None:
        """Persist cookies to config for a given user, environment, and domain
        with current timestamp.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.
            cookies (Dict[str, CacheEntry]): Mapping of cookie name to cache entry.

        Returns:
            None
        """
        section = (
            self.config_data.setdefault("users", {})
            .setdefault(user, {})
            .setdefault(env, {})
            .setdefault(domain, {})
        )
        cookies_list = []
        for name, entry in cookies.items():
            cookies_list.append(
                {
                    "name": name,
                    "value": entry.value,
                    "timestamp": entry.timestamp.isoformat(),
                }
            )
        section["cookies"] = cookies_list

    def prune_expired_cookies(self, user: str, env: str, domain: str) -> None:
        """Remove stale (expired) cookie entries from config for a given user,
        environment, and domain.

        Args:
            user (str): The user key.
            env (str): The environment key.
            domain (str): The domain key.

        Returns:
            None
        """
        section = (
            self.config_data.setdefault("users", {})
            .setdefault(user, {})
            .setdefault(env, {})
            .setdefault(domain, {})
        )
        ttl = section.get("ttl_seconds", 28800)
        now = datetime.now(timezone.utc)
        cookies = section.get("cookies", [])
        valid_cookies = []
        for cookie in cookies:
            if "name" in cookie and "value" in cookie and "timestamp" in cookie:
                ts = datetime.fromisoformat(cookie["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entry = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=ttl,
                )
                if entry.is_valid(now=now):
                    valid_cookies.append(
                        {
                            "name": cookie["name"],
                            "value": cookie["value"],
                            "timestamp": cookie["timestamp"],
                        }
                    )
        section["cookies"] = valid_cookies


def read_cookies_from_browser(driver: Any, domain: str) -> List[Dict[str, Any]]:
    """Extract cookies matching a given domain from the Selenium driver.

    Reads all cookies from the driver and filters those belonging to the specified
    domain. Handles domain matching flexibly to account for subdomains.

    Args:
        driver (Any): A Selenium WebDriver instance.
        domain (str): The domain to filter cookies by (e.g., 'example.com').

    Returns:
        List[Dict[str, Any]]: List of cookie dictionaries matching the domain.
            Each cookie has keys like 'name', 'value', 'domain', etc.

    Raises:
        AttributeError: If driver does not have a get_cookies() method.
    """
    try:
        all_cookies = driver.get_cookies()
    except AttributeError as e:
        raise AttributeError(f"Driver does not have get_cookies() method: {e}") from e

    filtered_cookies = [
        cookie for cookie in all_cookies if cookie.get("domain", "").endswith(domain)
    ]
    return filtered_cookies


def write_cookies_to_browser(
    driver: Any, cookies: List[Dict[str, Any]], domain: str
) -> None:
    """Inject cookies into the browser via the Selenium driver.

    Adds the given list of cookies to the browser session. Handles any exceptions
    that occur during cookie injection and logs them appropriately.

    Args:
        driver (Any): A Selenium WebDriver instance.
        cookies (List[Dict[str, Any]]): List of cookie dictionaries to inject.
            Each dictionary should have 'name' and 'value' keys at minimum.
        domain (str): The domain scope for the cookies (for reference/logging).

    Returns:
        None

    Raises:
        AttributeError: If driver does not have an add_cookie() method.
    """
    for cookie in cookies:
        try:
            driver.add_cookie(cookie)
        except AttributeError as e:
            raise AttributeError(
                f"Driver does not have add_cookie() method: {e}"
            ) from e
        except Exception:
            # Log or handle exceptions during individual cookie additions
            # Continue with remaining cookies rather than failing entirely
            pass


def get_applicable_rules(
    cookie_config: CookieConfig, domain: str, user: str, env: str
) -> List[CookieRule]:
    """Query the hierarchical configuration for cookie rules matching domain, user, env.

    Retrieves all cookie rules applicable to the given domain, user, and environment
    from the loaded configuration.

    Args:
        cookie_config (CookieConfig): The loaded cookie configuration object.
        domain (str): The domain key (e.g., 'example_com').
        user (str): The user key (e.g., 'alice').
        env (str): The environment key (e.g., 'prod').

    Returns:
        List[CookieRule]: List of applicable cookie rules for this context.
    """
    return cookie_config.get_rules(user, env, domain)


def inject_and_verify_cookies(
    launcher: Any, domain: str, user: str, env: str, cookie_config: CookieConfig
) -> None:
    """Main integration hook to inject cached cookies and verify authenticity.

    Performs the following workflow:
    1. Query cached cookies for the given domain, user, and environment.
    2. If valid cached cookies exist, inject them into the browser.
    3. Navigate to the domain to verify authentication.
    4. Read cookies back from the browser and update the cache.

    This function should be called after initial navigation or as a separate
    authentication verification step.

    Args:
        launcher (Any): A BrowserLauncher instance with a driver and logger.
        domain (str): The domain to operate on.
        user (str): The user context.
        env (str): The environment context.
        cookie_config (CookieConfig): The loaded cookie configuration.

    Returns:
        None

    Raises:
        AttributeError: If launcher lacks expected driver or logger attributes.
    """
    try:
        # Get valid cached cookies for this context
        valid_cache = cookie_config.get_valid_cookie_cache(user, env, domain)

        if valid_cache:
            launcher.logger.info(
                f"Found {len(valid_cache)} valid cached cookies for "
                f"{user}/{env}/{domain}"
            )
            # Convert cache entries to cookie dicts for injection
            cookies_to_inject = [
                {"name": name, "value": entry.value}
                for name, entry in valid_cache.items()
            ]
            # Inject cookies into the browser
            write_cookies_to_browser(launcher.driver, cookies_to_inject, domain)
        else:
            launcher.logger.info(
                f"No valid cached cookies found for {user}/{env}/{domain}"
            )

        # Read cookies back from the browser to verify or update cache
        browser_cookies = read_cookies_from_browser(launcher.driver, domain)

        if browser_cookies:
            launcher.logger.info(
                f"Read {len(browser_cookies)} cookies from browser for domain {domain}"
            )
            # Update cache with cookies from browser
            for cookie in browser_cookies:
                cookie_config.update_cookie_cache(
                    user, env, domain, cookie["name"], cookie.get("value", "")
                )

    except AttributeError as e:
        if hasattr(launcher, "logger") and launcher.logger:
            launcher.logger.error(
                f"Error during cookie injection/verification: {e}", exc_info=True
            )
        raise
    except Exception as e:
        if hasattr(launcher, "logger") and launcher.logger:
            launcher.logger.error(
                f"Unexpected error during cookie injection/verification: {e}",
                exc_info=True,
            )
