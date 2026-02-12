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

    def load_cookie_cache(self, user: str, env: str, domain: str) -> Dict[str, CacheEntry]:
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

    def save_cookie_cache(self, user: str, env: str, domain: str, cache: Dict[str, CacheEntry]) -> None:
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
            cookies_list.append({
                "name": name,
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
            })
        section["cookies"] = cookies_list


    def update_cookie_cache(self, user: str, env: str, domain: str, name: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        """Update a single cookie cache entry for a given user, environment, domain, and cookie name.

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
            cookies.append({
                "name": name,
                "value": value,
                "timestamp": now.isoformat(),
            })
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


    def get_valid_cookie_cache(self, user: str, env: str, domain: str) -> Dict[str, CacheEntry]:
        """Get only valid (non-expired) cookie cache entries for a given user, environment, and domain.

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

    def load_cookie_cache_from_config(self, user: str, env: str, domain: str) -> Dict[str, CacheEntry]:
        """Parse persisted cookies from config for a given user, environment, and domain.

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

    def save_cookies_to_cache(self, user: str, env: str, domain: str, cookies: Dict[str, CacheEntry]) -> None:
        """Persist cookies to config for a given user, environment, and domain with current timestamp.

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
            cookies_list.append({
                "name": name,
                "value": entry.value,
                "timestamp": entry.timestamp.isoformat(),
            })
        section["cookies"] = cookies_list

    def prune_expired_cookies(self, user: str, env: str, domain: str) -> None:
        """Remove stale (expired) cookie entries from config for a given user, environment, and domain.

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
                    valid_cookies.append({
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "timestamp": cookie["timestamp"],
                    })
        section["cookies"] = valid_cookies

