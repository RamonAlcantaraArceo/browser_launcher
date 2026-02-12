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
