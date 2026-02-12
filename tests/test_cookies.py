"""Unit tests for CookieRule, CacheEntry, and CookieConfig (Google-style docstrings)."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from browser_launcher.cookies import (
    CacheEntry,
    CookieConfig,
    CookieRule,
    get_applicable_rules,
    inject_and_verify_cookies,
    read_cookies_from_browser,
    write_cookies_to_browser,
)


def test_cookie_rule_fields():
    """Test CookieRule dataclass fields and defaults."""
    rule = CookieRule(domain="example.com", name="sessionid")
    assert rule.domain == "example.com"
    assert rule.name == "sessionid"
    assert rule.variants == {}
    assert rule.ttl_seconds is None


def test_cache_entry_validity():
    """Test CacheEntry validity based on TTL and timestamp."""
    now = datetime.now(timezone.utc)  # datetime.utcnow()
    entry = CacheEntry(value="abc", timestamp=now - timedelta(hours=1))
    assert entry.is_valid(now=now)
    expired = CacheEntry(value="abc", timestamp=now - timedelta(hours=9))
    assert not expired.is_valid(now=now)
    # Custom TTL
    short = CacheEntry(
        value="abc", timestamp=now - timedelta(seconds=30), ttl_seconds=10
    )
    assert not short.is_valid(now=now)


def test_cookie_config_get_rules_and_cache_entries():
    """Test CookieConfig rule and cache entry extraction from hierarchical config."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "alice": {
                "prod": {
                    "example_com": {
                        "cookies": [
                            {
                                "name": "sessionid",
                                "value": "abc",
                                "timestamp": now.isoformat(),
                            },
                            {"name": "auth", "variants": {"chrome": "auth_chrome"}},
                        ],
                        "ttl_seconds": 1000,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    rules = config.get_rules("alice", "prod", "example_com")
    assert len(rules) == 2
    assert rules[0].name == "sessionid"
    assert rules[1].variants == {"chrome": "auth_chrome"}
    entries = config.get_cache_entries("alice", "prod", "example_com")
    assert len(entries) == 1
    assert entries[0].value == "abc"
    assert entries[0].ttl_seconds == 1000
    assert entries[0].is_valid(now=now)


def test_load_cookie_cache_returns_dict_of_cache_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "bob": {
                "dev": {
                    "test_com": {
                        "cookies": [
                            {
                                "name": "token",
                                "value": "xyz",
                                "timestamp": now.isoformat(),
                            },
                            {
                                "name": "expired",
                                "value": "old",
                                "timestamp": (now - timedelta(hours=9)).isoformat(),
                            },
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    cache = config.load_cookie_cache("bob", "dev", "test_com")
    assert isinstance(cache, dict)
    assert "token" in cache
    assert isinstance(cache["token"], CacheEntry)
    assert cache["token"].value == "xyz"
    assert cache["token"].timestamp == now
    assert cache["token"].ttl_seconds == 28800
    assert "expired" in cache
    assert cache["expired"].value == "old"


def test_save_cookie_cache_updates_config_data():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "bob": {
                "dev": {
                    "test_com": {
                        "cookies": [],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    cache = {
        "token": CacheEntry(value="xyz", timestamp=now, ttl_seconds=28800),
        "session": CacheEntry(value="abc", timestamp=now, ttl_seconds=28800),
    }
    config.save_cookie_cache("bob", "dev", "test_com", cache)
    cookies = config_data["users"]["bob"]["dev"]["test_com"]["cookies"]
    assert len(cookies) == 2
    names = {c["name"] for c in cookies}
    assert "token" in names
    assert "session" in names
    for c in cookies:
        assert c["value"] in ["xyz", "abc"]
        assert c["timestamp"] == now.isoformat()


def test_update_cookie_cache_adds_and_modifies_entry():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "bob": {
                "dev": {
                    "test_com": {
                        "cookies": [
                            {
                                "name": "token",
                                "value": "xyz",
                                "timestamp": (now - timedelta(hours=1)).isoformat(),
                            }
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    # Update existing
    config.update_cookie_cache(
        "bob", "dev", "test_com", "token", "newval", ttl_seconds=1000
    )
    cookies = config_data["users"]["bob"]["dev"]["test_com"]["cookies"]
    token_cookie = next(c for c in cookies if c["name"] == "token")
    assert token_cookie["value"] == "newval"
    assert token_cookie["timestamp"]  # Should be updated to now
    # Add new
    config.update_cookie_cache("bob", "dev", "test_com", "session", "abc")
    session_cookie = next(c for c in cookies if c["name"] == "session")
    assert session_cookie["value"] == "abc"
    assert session_cookie["timestamp"]


def test_clear_cookie_cache_removes_all_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "bob": {
                "dev": {
                    "test_com": {
                        "cookies": [
                            {
                                "name": "token",
                                "value": "xyz",
                                "timestamp": now.isoformat(),
                            }
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    config.clear_cookie_cache("bob", "dev", "test_com")
    cookies = config_data["users"]["bob"]["dev"]["test_com"]["cookies"]
    assert cookies == []


def test_get_valid_cookie_cache_filters_expired_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "bob": {
                "dev": {
                    "test_com": {
                        "cookies": [
                            {
                                "name": "token",
                                "value": "xyz",
                                "timestamp": now.isoformat(),
                            },
                            {
                                "name": "expired",
                                "value": "old",
                                "timestamp": (now - timedelta(hours=9)).isoformat(),
                            },
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    valid_cache = config.get_valid_cookie_cache("bob", "dev", "test_com")
    assert "token" in valid_cache
    assert "expired" not in valid_cache
    assert valid_cache["token"].is_valid(now=now)


def test_load_cookie_cache_from_config_returns_dict_of_cache_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "carol": {
                "stage": {
                    "demo_com": {
                        "cookies": [
                            {
                                "name": "session",
                                "value": "val",
                                "timestamp": now.isoformat(),
                            },
                            {
                                "name": "expired",
                                "value": "old",
                                "timestamp": (now - timedelta(hours=9)).isoformat(),
                            },
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    cache = config.load_cookie_cache_from_config("carol", "stage", "demo_com")
    assert isinstance(cache, dict)
    assert "session" in cache
    assert cache["session"].value == "val"
    assert cache["session"].timestamp == now
    assert cache["session"].ttl_seconds == 28800
    assert "expired" in cache
    assert cache["expired"].value == "old"


def test_save_cookies_to_cache_persists_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "carol": {
                "stage": {
                    "demo_com": {
                        "cookies": [],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    cookies = {
        "session": CacheEntry(value="val", timestamp=now, ttl_seconds=28800),
        "token": CacheEntry(value="tok", timestamp=now, ttl_seconds=28800),
    }
    config.save_cookies_to_cache("carol", "stage", "demo_com", cookies)
    persisted = config_data["users"]["carol"]["stage"]["demo_com"]["cookies"]
    assert len(persisted) == 2
    names = {c["name"] for c in persisted}
    assert "session" in names
    assert "token" in names
    for c in persisted:
        assert c["value"] in ["val", "tok"]
        assert c["timestamp"] == now.isoformat()


def test_prune_expired_cookies_removes_stale_entries():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data = {
        "users": {
            "carol": {
                "stage": {
                    "demo_com": {
                        "cookies": [
                            {
                                "name": "session",
                                "value": "val",
                                "timestamp": now.isoformat(),
                            },
                            {
                                "name": "expired",
                                "value": "old",
                                "timestamp": (now - timedelta(hours=9)).isoformat(),
                            },
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)
    config.prune_expired_cookies("carol", "stage", "demo_com")
    cookies = config_data["users"]["carol"]["stage"]["demo_com"]["cookies"]
    assert len(cookies) == 1
    assert cookies[0]["name"] == "session"


def test_read_cookies_from_browser():
    """Test reading cookies from Selenium driver filtered by domain."""
    mock_driver = MagicMock()
    mock_driver.get_cookies.return_value = [
        {"name": "session", "value": "abc123", "domain": "example.com"},
        {"name": "token", "value": "xyz789", "domain": "example.com"},
        {"name": "other", "value": "def456", "domain": "other.com"},
    ]

    cookies = read_cookies_from_browser(mock_driver, "example.com")

    assert len(cookies) == 2
    assert cookies[0]["name"] == "session"
    assert cookies[1]["name"] == "token"
    mock_driver.get_cookies.assert_called_once()


def test_read_cookies_from_browser_empty():
    """Test reading cookies when none match the domain."""
    mock_driver = MagicMock()
    mock_driver.get_cookies.return_value = [
        {"name": "other", "value": "def456", "domain": "other.com"},
    ]

    cookies = read_cookies_from_browser(mock_driver, "example.com")

    assert len(cookies) == 0


def test_write_cookies_to_browser():
    """Test injecting cookies into Selenium driver."""
    mock_driver = MagicMock()
    cookies = [
        {"name": "session", "value": "abc123"},
        {"name": "token", "value": "xyz789"},
    ]

    write_cookies_to_browser(mock_driver, cookies, "example.com")

    assert mock_driver.add_cookie.call_count == 2
    mock_driver.add_cookie.assert_any_call({"name": "session", "value": "abc123"})
    mock_driver.add_cookie.assert_any_call({"name": "token", "value": "xyz789"})


def test_write_cookies_to_browser_empty():
    """Test writing empty cookie list (no-op)."""
    mock_driver = MagicMock()

    write_cookies_to_browser(mock_driver, [], "example.com")

    mock_driver.add_cookie.assert_not_called()


def test_get_applicable_rules():
    """Test getting applicable cookie rules from hierarchical config."""
    config_data = {
        "users": {
            "alice": {
                "prod": {
                    "example_com": {
                        "cookies": [
                            {
                                "name": "sessionid",
                                "variants": {"chrome": "sid_chrome"},
                            },
                            {"name": "auth"},
                        ],
                        "ttl_seconds": 1000,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)

    rules = get_applicable_rules(config, "example_com", "alice", "prod")

    assert len(rules) == 2
    assert rules[0].name == "sessionid"
    assert rules[0].variants == {"chrome": "sid_chrome"}
    assert rules[1].name == "auth"


def test_get_applicable_rules_not_found():
    """Test getting rules for non-existent user/env/domain."""
    config_data: dict[str, dict] = {"users": {}}
    config = CookieConfig(config_data)

    rules = get_applicable_rules(config, "example_com", "alice", "prod")

    assert len(rules) == 0


def test_inject_and_verify_cookies():
    """Test the main integration hook for cookie injection and verification."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    config_data: dict[str, dict] = {
        "users": {
            "alice": {
                "prod": {
                    "example_com": {
                        "cookies": [
                            {
                                "name": "sessionid",
                                "value": "cached_session",
                                "timestamp": now.isoformat(),
                            }
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)

    # Mock the launcher with driver and logger
    mock_launcher = MagicMock()
    mock_driver = MagicMock()
    mock_launcher.driver = mock_driver
    mock_driver.get_cookies.return_value = [
        {"name": "sessionid", "value": "cached_session", "domain": "example.com"},
        {"name": "new_cookie", "value": "new_value", "domain": "example.com"},
    ]

    inject_and_verify_cookies(mock_launcher, "example_com", "alice", "prod", config)

    # Verify that cookies were read and injected
    mock_driver.get_cookies.assert_called()
    mock_driver.add_cookie.assert_called()


def test_inject_and_verify_cookies_expired():
    """Test injection hook with expired cached cookies (should not inject)."""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expired_time = now - timedelta(hours=10)
    config_data: dict[str, dict] = {
        "users": {
            "alice": {
                "prod": {
                    "example_com": {
                        "cookies": [
                            {
                                "name": "sessionid",
                                "value": "expired_session",
                                "timestamp": expired_time.isoformat(),
                            }
                        ],
                        "ttl_seconds": 28800,
                    }
                }
            }
        }
    }
    config = CookieConfig(config_data)

    mock_launcher = MagicMock()
    mock_driver = MagicMock()
    mock_launcher.driver = mock_driver

    inject_and_verify_cookies(mock_launcher, "example_com", "alice", "prod", config)

    # With expired cookies, should not attempt to add cookies
    # Verify that logger handling worked (either info or warning)
    assert mock_launcher.logger.info.called or mock_launcher.logger.warning.called
