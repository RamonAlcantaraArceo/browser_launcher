"""Test hierarchical cookie rule lookup in BrowserLauncherConfig."""

import tempfile
from pathlib import Path

import toml

from browser_launcher.config import BrowserLauncherConfig


def test_get_cookie_rules_returns_rules():
    """Should return cookie rules for a valid hierarchical section."""
    # Create a temporary config file with hierarchical cookie section
    config_dict: dict = {
        "users": {
            "alice": {
                "staging": {
                    "example_com": {
                        "cookies": [
                            {
                                "name": "session_id",
                                "value": "abc123",
                                "timestamp": "2026-02-11T10:00:00Z",
                            },
                            {
                                "name": "auth_token",
                                "value": "token456",
                                "timestamp": "2026-02-11T10:00:00Z",
                            },
                        ]
                    }
                }
            }
        }
    }
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        toml.dump(config_dict, tmp)
        tmp_path = Path(tmp.name)
    config = BrowserLauncherConfig(config_path=tmp_path)
    section = "users.alice.staging.example_com"
    rules = config.get_cookie_rules(section)
    assert isinstance(rules, list)
    assert len(rules) == 2
    assert rules[0]["name"] == "session_id"
    tmp_path.unlink()


def test_get_cookie_rules_empty_for_missing_section():
    """Should return empty list if section does not exist."""
    config_dict: dict = {"users": {}}
    with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
        toml.dump(config_dict, tmp)
        tmp_path = Path(tmp.name)
    config = BrowserLauncherConfig(config_path=tmp_path)
    section = "users.bob.prod.example_com"
    rules = config.get_cookie_rules(section)
    assert rules == []
    tmp_path.unlink()
