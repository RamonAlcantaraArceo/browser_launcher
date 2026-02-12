"""Unit tests for CookieRule, CacheEntry, and CookieConfig (Google-style docstrings)."""

from datetime import datetime, timedelta, timezone

from browser_launcher.cookies import CacheEntry, CookieConfig, CookieRule


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
    config.update_cookie_cache("bob", "dev", "test_com", "token", "newval", ttl_seconds=1000)
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