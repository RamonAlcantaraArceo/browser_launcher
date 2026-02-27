"""
Cookie management module for browser_launcher.

Provides dataclasses and configuration loader for hierarchical, user/env/domain-aware
cookie rules and cache.
All docstrings use Google-style format.
"""

import logging
import textwrap
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml
from rich.table import Table
from selenium import webdriver

logger = logging.getLogger(__name__)


def config_key_to_domain(key: str) -> str:
    """Convert config domain key (underscores) to real domain (dots)."""
    return key.replace("_", ".")


def domain_to_config_key(domain: str) -> str:
    """Convert real domain (dots) to config domain key (underscores)."""
    return domain.replace(".", "_")


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
    domain: str = ""

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
        section = self.config_data.get("users", {}).get(user, {}).get(env, {})
        rules = []
        cookies = section.get("cookies", {})
        for name, cookie in cookies.items():
            if cookie.get("domain") == domain:
                rules.append(
                    CookieRule(
                        domain=domain,
                        name=name,
                        variants=cookie.get("variants", {}),
                        ttl_seconds=cookie.get("ttl_seconds", 28800),
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
        section = self.config_data.get("users", {}).get(user, {}).get(env, {})
        entries = []
        cookies = section.get("cookies", {})
        logger.debug(
            f"Loading cache entries for {user}/{env}/{domain}. Found cookies: "
            f"{list(cookies.keys())}"
        )
        for name, cookie in cookies.items():
            if cookie.get("domain") == domain and (
                "value" in cookie
                and "timestamp" in cookie
                and cookie["value"] != "..."
                and cookie["timestamp"] != "..."
            ):
                try:
                    ts = datetime.fromisoformat(cookie["timestamp"])
                except Exception:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entries.append(
                    CacheEntry(
                        value=cookie["value"],
                        timestamp=ts,
                        ttl_seconds=cookie.get("ttl_seconds", 28800),
                    )
                )

        logger.info(f"Loaded {len(entries)} cache entries for {user}/{env}/{domain}.")
        logger.debug(f"Cache entries: {entries}")
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
        section = self.config_data.get("users", {}).get(user, {}).get(env, {})
        cache: Dict[str, CacheEntry] = {}
        cookies = section.get("cookies", {})
        for name, cookie in cookies.items():
            if cookie.get("domain") == domain and (
                "value" in cookie
                and "timestamp" in cookie
                and cookie["value"] != "..."
                and cookie["timestamp"] != "..."
            ):
                try:
                    ts = datetime.fromisoformat(cookie["timestamp"])
                except Exception:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                cache[name] = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=cookie.get("ttl_seconds", 28800),
                    domain=domain,
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
        )
        cookies_dict = section.setdefault("cookies", {})
        for name, entry in cache.items():
            cookies_dict[name] = {
                "domain": domain,
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
            }
        section["cookies"] = cookies_dict

        logger.info(
            f"Saved cookie cache for {user}/{env}/{domain} with {len(cache)} entries."
        )

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
        )
        cookies = section.setdefault("cookies", {})
        now = datetime.now(timezone.utc)
        cookies[name] = {
            "domain": domain,
            "value": value,
            "timestamp": now.isoformat(),
        }
        if ttl_seconds is not None:
            cookies[name]["ttl_seconds"] = ttl_seconds

        logger.info(f"Updated cookie cache for {user}/{env}/{domain}: {name}")

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
        )
        cookies = section.get("cookies", {})
        # Remove all cookies matching this domain
        names_to_remove = [
            name for name, cookie in cookies.items() if cookie.get("domain") == domain
        ]
        for name in names_to_remove:
            del cookies[name]

        logger.info(f"Cleared cookie cache for {user}/{env}/{domain}.")

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
        section = self.config_data.get("users", {}).get(user, {}).get(env, {})
        cache: Dict[str, CacheEntry] = {}
        cookies = section.get("cookies", {})
        for name, cookie in cookies.items():
            if cookie.get("domain") == domain and (
                "value" in cookie
                and "timestamp" in cookie
                and cookie["value"] != "..."
                and cookie["timestamp"] != "..."
            ):
                try:
                    ts = datetime.fromisoformat(cookie["timestamp"])
                except Exception:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                cache[name] = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=cookie.get("ttl_seconds", 28800),
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
        )
        cookies_dict = section.setdefault("cookies", {})
        for name, entry in cookies.items():
            cookies_dict[name] = {
                "domain": domain,
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
            }
        section["cookies"] = cookies_dict

        logger.info(
            f"Saved cookies to cache for {user}/{env}/{domain} with "
            f"{len(cookies)} entries."
        )

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
        )
        now = datetime.now(timezone.utc)
        cookies = section.get("cookies", {})
        valid_cookies = {}
        for name, cookie in cookies.items():
            if cookie.get("domain") == domain and (
                "value" in cookie
                and "timestamp" in cookie
                and cookie["value"] != "..."
                and cookie["timestamp"] != "..."
            ):
                try:
                    ts = datetime.fromisoformat(cookie["timestamp"])
                except Exception:
                    continue
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                entry = CacheEntry(
                    value=cookie["value"],
                    timestamp=ts,
                    ttl_seconds=cookie.get("ttl_seconds", 28800),
                )
                if entry.is_valid(now=now):
                    valid_cookies[name] = cookie
            else:
                # Keep cookies for other domains
                valid_cookies[name] = cookie
        section["cookies"] = valid_cookies

        logger.info(
            f"Pruned expired cookies for {user}/{env}/{domain}. "
            f"Remaining: "
            f"{len([c for c in valid_cookies.values() if c.get('domain') == domain])}."
        )


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

    # Convert config key to real domain for filtering
    filtered_cookies = []
    excluded_cookies = []
    for cookie in all_cookies:
        cookie_domain = cookie.get("domain", "")
        if cookie_domain.endswith(domain):
            filtered_cookies.append(cookie)
            logger.debug(
                f"Including cookie '{cookie.get('name')}' with domain "
                f"'{cookie_domain}' for filter '{domain}'."
            )
        else:
            excluded_cookies.append(cookie)
            logger.debug(
                f"Excluding cookie '{cookie.get('name')}' with domain "
                f"'{cookie_domain}' for filter '{domain}'."
            )
    logger.info(
        f"Read {len(filtered_cookies)} cookies for domain '{domain}' from browser."
    )
    summary = [
        {
            "name": c.get("name"),
            "domain": c.get("domain"),
            "value": c.get("value", "")[:4],
        }
        for c in filtered_cookies
    ]

    indented = textwrap.indent(yaml.dump(summary, sort_keys=False), "  ")  # two spaces

    logger.debug("Cookies read from browser (summary):\n%s", indented)

    return filtered_cookies


def write_cookies_to_browser(
    driver: webdriver.Ie, cookies: List[Dict[str, Any]]
) -> None:
    """Inject cookies into the browser via the Selenium driver.

    Adds the given list of cookies to the browser session. Handles any exceptions
    that occur during cookie injection and logs them appropriately.

    Args:
        driver (webdriver.Ie): A Selenium WebDriver instance.
        cookies (List[Dict[str, Any]]): List of cookie dictionaries to inject.
            Each dictionary should have 'name' and 'value' keys at minimum.
        domain (str): The domain scope for the cookies (for reference/logging).

    Returns:
        None

    Raises:
        AttributeError: If driver does not have an add_cookie() method.
    """
    for cookie in cookies:
        cookie_to_add = cookie.copy()
        # Do NOT set the domain field; let Selenium use the current page's domain
        poped_domain = cookie_to_add.pop("domain", None)
        try:
            if driver.get_cookie(
                cookie_to_add["name"]
            ):  # Check if cookie already exists
                driver.delete_cookie(
                    cookie_to_add["name"]
                )  # Remove existing cookie before adding
                logger.debug(
                    f"Deleted existing cookie '{cookie_to_add['name']}'"
                    " before adding cached"
                )

            driver.add_cookie(cookie_to_add)
            logger.debug(
                f"Injected cookie '{cookie.get('name')}' for domain "
                f"'{poped_domain}' into browser."
            )
        except AttributeError as e:
            raise AttributeError(
                f"Driver does not have add_cookie() method: {e}"
            ) from e
        except Exception:
            # Log or handle exceptions during individual cookie additions
            # Continue with remaining cookies rather than failing entirely
            logger.error(
                f"Failed to inject cookie '{cookie.get('name')}' for "
                f"domain '{poped_domain}'",
                exc_info=True,
            )
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
    launcher: Any, user: str, env: str, cookie_config: CookieConfig
) -> Optional[List[Dict[str, Any]]]:
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
        user (str): The user context.
        env (str): The environment context.
        cookie_config (CookieConfig): The loaded cookie configuration.

    Returns:
        Optional[List[Dict[str, Any]]]: The cookies that were injected, or None.

    Raises:
        AttributeError: If launcher lacks expected driver or logger attributes.
    """
    cookies_to_inject: Optional[List[Dict[str, Any]]] = None
    try:
        target_domains = [
            val["domain"]
            for val in cookie_config.config_data["users"][user][env]["cookies"].values()
        ]

        valid_cache = {}
        for target_domain in target_domains:
            cache_dict = cookie_config.get_valid_cookie_cache(user, env, target_domain)
            valid_cache.update(cache_dict)

        if valid_cache:
            logger.info(
                f"Found {len(valid_cache)} valid cached cookies for "
                f"{user}/{env}:{target_domains}"
            )

            # Convert cache entries to cookie dicts for injection
            cookies_to_inject = [
                {"name": name, "value": entry.value, "domain": entry.domain}
                for name, entry in valid_cache.items()
            ]

            # Inject cookies into the browser
            write_cookies_to_browser(launcher.driver, cookies_to_inject)
        else:
            logger.info(
                f"No valid cached cookies found for {user}/{env}:{target_domains}"
            )

        # Read cookies back from the browser to verify or update cache
        browser_cookies: List[Dict[str, Any]] = []
        for domain in target_domains:
            browser_cookie_list = read_cookies_from_browser(launcher.driver, domain)
            for cookie_entry in browser_cookie_list:
                if not any(
                    browser_cookie["name"] == cookie_entry["name"]
                    for browser_cookie in browser_cookies
                ) and cookie_entry.get("name") in list(valid_cache.keys()):
                    browser_cookies.append(cookie_entry)

        if browser_cookies:
            logger.info(
                f"Read {len(browser_cookies)} cookies from browser for"
                f" domain {target_domains}"
            )
            # Update cache with cookies from browser
            for cookie in browser_cookies:
                cookie_config.update_cookie_cache(
                    user,
                    env,
                    cookie.get("domain", ""),
                    cookie["name"],
                    cookie.get("value", ""),
                )

    except AttributeError as e:
        logger.error(f"Error during cookie injection/verification: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during cookie injection/verification: {e}",
            exc_info=True,
        )
        raise

    return cookies_to_inject


def _format_cookie_expiry(expiry: Any) -> str:
    """Format cookie expiry timestamp as a readable relative duration."""
    if expiry is None:
        return "session"

    try:
        expiry_ts = float(expiry)
    except (TypeError, ValueError):
        return "invalid"

    remaining_seconds = int(expiry_ts - time.time())
    if remaining_seconds <= 0:
        return "expired"
    if remaining_seconds < 60:
        return f"+{remaining_seconds}s"
    if remaining_seconds < 3600:
        minutes = remaining_seconds // 60
        return f"+{minutes}m"
    if remaining_seconds < 86400:
        hours = (remaining_seconds + 1800) // 3600
        return f"+{hours}h"

    days = (remaining_seconds + 43200) // 86400
    return f"+{days}d"


def _dump_cookies_from_browser(
    driver: Any,
    logger: logging.Logger,
    console: Any,
) -> None:
    """Dump cookies from the browser for the current domain.

    Args:
        driver: The browser driver instance.
        logger: Logger instance for logging.
        console: Console instance for user output.
    """
    browser_cookies = read_cookies_from_browser(driver, "")
    try:
        current_url = getattr(driver, "current_url", "")
        parsed_url = urlparse(current_url)
        effective_domain = parsed_url.netloc or parsed_url.path.split("/")[0]

        table = Table(
            title=f"Cookies from browser for domain {effective_domain or '*'}"
        )
        table.add_column("#", justify="right")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Value (first 6 chars)", style="magenta")
        table.add_column("Domain")
        table.add_column("Path")
        table.add_column("Secure")
        table.add_column("HttpOnly")
        table.add_column("SameSite")
        table.add_column("Expiry")
        sorted_cookies = sorted(
            browser_cookies,
            key=lambda cookie: str(cookie.get("name", "")).lower(),
        )
        for index, cookie in enumerate(sorted_cookies, start=1):
            value_preview = cookie["value"][:6] if cookie.get("value") else ""
            table.add_row(
                str(index),
                cookie.get("name", ""),
                f"{value_preview}..." if value_preview else "",
                str(cookie.get("domain", "")),
                str(cookie.get("path", "")),
                "yes" if bool(cookie.get("secure", False)) else "no",
                "yes" if bool(cookie.get("httpOnly", False)) else "no",
                str(cookie.get("sameSite", "")),
                _format_cookie_expiry(cookie.get("expiry")),
            )
        console.print(table)
        logger.info(
            f"Dumped {len(browser_cookies)} cookies from browser for "
            f"domain {effective_domain}"
        )
    except Exception as e:
        console.print(f"❌ Error reading cookies: {e}")
        logger.error(f"Error reading cookies: {e}", exc_info=True)
