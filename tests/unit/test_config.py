"""Unit tests for BrowserLauncherConfig (config.py)."""

from pathlib import Path

import pytest
import toml

from browser_launcher.config import BrowserLauncherConfig

# Minimal valid config for tests
default_config = {
    "general": {"default_browser": "chrome"},
    "urls": {"homepage": "https://example.com"},
    "logging": {"console_logging": True},
    "browsers": {
        "chrome": {
            "binary_path": "/usr/bin/google-chrome",
            "headless": False,
            "user_data_dir": "/tmp/profile",
            "custom_flags": ["--flag1"],
            "extra_options": {"foo": "bar"},
        }
    },
}


def write_config(tmp_path, config_dict):
    config_path = tmp_path / "config.toml"
    with open(config_path, "w") as f:
        toml.dump(config_dict, f)
    return config_path


@pytest.mark.unit
def test_loads_config_and_properties(tmp_path):
    config_path = write_config(tmp_path, default_config)
    config = BrowserLauncherConfig(config_path)
    assert config.get_default_browser() == "chrome"
    assert config.get_default_url() == "https://example.com"
    assert config.get_console_logging() is True


@pytest.mark.unit
def test_get_browser_config_returns_browserconfig(tmp_path):
    config_path = write_config(tmp_path, default_config)
    config = BrowserLauncherConfig(config_path)
    browser_config = config.get_browser_config("chrome")
    assert browser_config.binary_path == Path("/usr/bin/google-chrome")
    assert browser_config.headless is False
    assert browser_config.user_data_dir == Path("/tmp/profile")
    assert browser_config.custom_flags == ["--flag1"]
    assert browser_config.extra_options == {"foo": "bar"}


@pytest.mark.unit
def test_get_console_logging_defaults_to_false(tmp_path):
    config_dict = dict(default_config)
    config_dict["logging"] = {}  # Remove console_logging
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)
    assert config.get_console_logging() is False


@pytest.mark.unit
def test_get_logging_level_defaults_to_warning(tmp_path):
    config_dict = dict(default_config)
    config_dict["logging"] = {"default_log_level": "WARNING"}
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)
    assert config.get_logging_level() == "WARNING"


@pytest.mark.unit
def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        BrowserLauncherConfig(Path("/nonexistent/path/config.toml"))


@pytest.mark.unit
def test_get_browser_config_handles_missing_browser(tmp_path):
    config_path = write_config(tmp_path, default_config)
    config = BrowserLauncherConfig(config_path)
    # Should return a BrowserConfig with mostly None/empty values
    browser_config = config.get_browser_config("firefox")
    assert browser_config.binary_path is None
    assert browser_config.headless is False
    assert browser_config.user_data_dir is None
    assert browser_config.custom_flags is None or browser_config.custom_flags == []
    assert browser_config.extra_options == {}


@pytest.mark.unit
def test_get_cookie_rules_hierarchical_and_missing_paths(tmp_path):
    """Test cookie rule lookup for existing and missing hierarchical sections."""
    config_dict = dict(default_config)
    config_dict["users"] = {
        "alice": {
            "prod": {
                "example_com": {
                    "cookies": [
                        {"name": "session", "required": True},
                        {"name": "csrftoken", "required": False},
                    ]
                },
                "no_cookies": {},
            }
        }
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    rules = config.get_cookie_rules("users.alice.prod.example_com")
    assert len(rules) == 2
    assert rules[0]["name"] == "session"

    empty_rules = config.get_cookie_rules("users.alice.prod.no_cookies")
    assert empty_rules == []

    missing_rules = config.get_cookie_rules("users.alice.prod.missing_com")
    assert missing_rules == []

    missing_branch = config.get_cookie_rules("users.bob.dev.example.com")
    assert missing_branch == []


# Authentication configuration tests
@pytest.mark.unit
def test_get_auth_config_global_defaults(tmp_path):
    """Test getting global authentication configuration."""
    config_dict = dict(default_config)
    config_dict["auth"] = {
        "timeout_seconds": 45,
        "retry_attempts": 2,
        "headless": True,
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    auth_config = config.get_auth_config()
    assert auth_config.timeout_seconds == 45
    assert auth_config.retry_attempts == 2
    assert auth_config.headless is True


@pytest.mark.unit
def test_get_auth_config_converts_screenshot_directory_to_path(tmp_path):
    """Test screenshot_directory string is converted into a Path object."""
    config_dict = dict(default_config)
    config_dict["auth"] = {
        "timeout_seconds": 45,
        "retry_attempts": 2,
        "screenshot_directory": "/tmp/auth_screens",
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    auth_config = config.get_auth_config()
    assert isinstance(auth_config.screenshot_directory, Path)
    assert auth_config.screenshot_directory == Path("/tmp/auth_screens")


@pytest.mark.unit
def test_get_auth_config_module_specific(tmp_path):
    """Test getting module-specific authentication configuration."""
    config_dict = dict(default_config)
    config_dict["auth"] = {
        "timeout_seconds": 45,
        "retry_attempts": 2,
        "headless": True,
        "form_auth": {
            "timeout_seconds": 60,
            "retry_attempts": 1,
            "credentials": {"username_field": "email"},
        },
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    # Test module-specific config overrides global
    form_auth_config = config.get_auth_config(module_name="form_auth")
    assert form_auth_config.timeout_seconds == 60  # Override global
    assert form_auth_config.retry_attempts == 1  # Override global
    assert form_auth_config.headless is True  # Inherit global


@pytest.mark.unit
def test_get_auth_config_user_env_hierarchy(tmp_path):
    """Test hierarchical user/environment authentication configuration."""
    config_dict = dict(default_config)
    config_dict.update(
        {
            "auth": {
                "timeout_seconds": 45,
                "retry_attempts": 2,
                "headless": True,
            },
            "users": {
                "alice": {
                    "prod": {
                        "auth": {
                            "timeout_seconds": 30,
                            "screenshot_on_failure": True,
                        }
                    }
                }
            },
        }
    )
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    # Test user/env config overrides global
    user_auth_config = config.get_auth_config(user="alice", env="prod")
    assert user_auth_config.timeout_seconds == 30  # Override global
    assert user_auth_config.retry_attempts == 2  # Inherit global
    assert user_auth_config.screenshot_on_failure is True  # User-specific


@pytest.mark.unit
def test_get_auth_config_full_hierarchy(tmp_path):
    """Test complete hierarchical configuration with module, user, and env."""
    config_dict = dict(default_config)
    config_dict.update(
        {
            "auth": {
                "timeout_seconds": 45,
                "retry_attempts": 2,
                "headless": True,
                "form_auth": {
                    "timeout_seconds": 60,
                    "retry_attempts": 1,
                    "credentials": {"username_field": "email"},
                },
            },
            "users": {
                "alice": {
                    "prod": {
                        "auth": {
                            "timeout_seconds": 30,
                            "screenshot_on_failure": True,
                            "form_auth": {
                                "timeout_seconds": 90,
                                "credentials": {"username": "alice@example.com"},
                            },
                        }
                    }
                }
            },
        }
    )
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    # Test complete hierarchy: global -> module -> user/env -> user/env/module
    hierarchical_config = config.get_auth_config(
        module_name="form_auth", user="alice", env="prod"
    )
    assert hierarchical_config.timeout_seconds == 90  # User module override
    assert hierarchical_config.retry_attempts == 1  # Module-specific override
    assert hierarchical_config.screenshot_on_failure is True  # Inherit user-level


@pytest.mark.unit
def test_get_auth_config_missing_sections(tmp_path):
    """Test authentication config with missing sections returns defaults."""
    config_path = write_config(tmp_path, default_config)  # No auth section
    config = BrowserLauncherConfig(config_path)

    # Should return AuthConfig with defaults when no auth section exists
    auth_config = config.get_auth_config()
    assert auth_config.timeout_seconds == 30  # AuthConfig default
    assert auth_config.retry_attempts == 1  # AuthConfig default
    assert auth_config.headless is True  # AuthConfig default

    # Test with non-existent user/env
    user_config = config.get_auth_config(user="nonexistent", env="missing")
    assert user_config.timeout_seconds == 30  # Should still return defaults


@pytest.mark.unit
def test_get_auth_module_config(tmp_path):
    """Test getting module-specific authentication configuration."""
    config_dict = dict(default_config)
    config_dict["auth"] = {
        "form_auth": {
            "timeout_seconds": 60,
            "credentials": {"username_field": "email"},
        },
        "oauth": {"timeout_seconds": 120, "credentials": {"client_id": "test_client"}},
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    # Test module retrieval
    form_auth_module = config.get_auth_module_config("form_auth")
    assert form_auth_module["timeout_seconds"] == 60
    assert form_auth_module["credentials"]["username_field"] == "email"

    oauth_module = config.get_auth_module_config("oauth")
    assert oauth_module["timeout_seconds"] == 120
    assert oauth_module["credentials"]["client_id"] == "test_client"

    # Test missing module returns empty dict
    missing_module = config.get_auth_module_config("nonexistent")
    assert missing_module == {}


@pytest.mark.unit
def test_get_available_auth_modules(tmp_path):
    """Test getting all available authentication modules."""
    config_dict = dict(default_config)
    config_dict["auth"] = {
        "timeout_seconds": 30,  # Global setting (not a module)
        "retry_attempts": 2,  # Global setting (not a module)
        "form_auth": {
            "timeout_seconds": 60,
            "credentials": {"username_field": "email"},
        },
        "oauth": {"timeout_seconds": 120, "credentials": {"client_id": "test_client"}},
    }
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    modules = config.get_available_auth_modules()
    assert "form_auth" in modules
    assert "oauth" in modules
    assert modules["form_auth"]["timeout_seconds"] == 60
    assert modules["oauth"]["timeout_seconds"] == 120

    # Verify global settings are not included as modules
    assert "timeout_seconds" not in modules
    assert "retry_attempts" not in modules


@pytest.mark.unit
def test_get_available_auth_modules_empty_auth_section(tmp_path):
    """Test getting modules when auth section is empty or missing."""
    config_path = write_config(tmp_path, default_config)  # No auth section
    config = BrowserLauncherConfig(config_path)

    modules = config.get_available_auth_modules()
    assert modules == {}

    # Test with empty auth section
    config_dict = dict(default_config)
    config_dict["auth"] = {}
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)

    modules = config.get_available_auth_modules()
    assert modules == {}


@pytest.mark.unit
def test_default_config_toml_auth_section_loads_valid_auth_config():
    """Verify the shipped default_config.toml produces a valid AuthConfig."""
    default_config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "browser_launcher"
        / "assets"
        / "default_config.toml"
    )
    assert default_config_path.exists(), (
        f"default_config.toml not found: {default_config_path}"
    )

    config = BrowserLauncherConfig(default_config_path)
    auth_config = config.get_auth_config()

    # Should match the values in default_config.toml [auth] section
    assert auth_config.timeout_seconds == 30
    assert auth_config.retry_attempts == 3
    assert auth_config.retry_delay_seconds == 1.0
    assert auth_config.headless is True
    assert auth_config.page_load_timeout == 20
    assert auth_config.element_wait_timeout == 10
    assert auth_config.screenshot_on_failure is False

    # Fields not set in [auth] should keep AuthConfig dataclass defaults
    assert auth_config.credentials == {}
    assert auth_config.custom_options == {}
    assert auth_config.user_agent is None
    assert auth_config.window_size == (1920, 1080)
    assert auth_config.screenshot_directory is None
    assert auth_config.allowed_domains == []
    assert auth_config.required_cookies == []


@pytest.mark.unit
def test_default_config_toml_has_no_module_configs_by_default():
    """Shipped default_config.toml should have no active module configs."""
    default_config_path = (
        Path(__file__).parent.parent.parent
        / "src"
        / "browser_launcher"
        / "assets"
        / "default_config.toml"
    )
    config = BrowserLauncherConfig(default_config_path)
    modules = config.get_available_auth_modules()
    assert modules == {}, f"Expected no active module configs, got: {modules}"
