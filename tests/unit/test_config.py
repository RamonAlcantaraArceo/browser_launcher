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


def test_loads_config_and_properties(tmp_path):
    config_path = write_config(tmp_path, default_config)
    config = BrowserLauncherConfig(config_path)
    assert config.get_default_browser() == "chrome"
    assert config.get_default_url() == "https://example.com"
    assert config.get_console_logging() is True


def test_get_browser_config_returns_browserconfig(tmp_path):
    config_path = write_config(tmp_path, default_config)
    config = BrowserLauncherConfig(config_path)
    browser_config = config.get_browser_config("chrome")
    assert browser_config.binary_path == Path("/usr/bin/google-chrome")
    assert browser_config.headless is False
    assert browser_config.user_data_dir == Path("/tmp/profile")
    assert browser_config.custom_flags == ["--flag1"]
    assert browser_config.extra_options == {"foo": "bar"}


def test_get_console_logging_defaults_to_false(tmp_path):
    config_dict = dict(default_config)
    config_dict["logging"] = {}  # Remove console_logging
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)
    assert config.get_console_logging() is False


def test_get_logging_level_defaults_to_warning(tmp_path):
    config_dict = dict(default_config)
    config_dict["logging"] = {"default_log_level": "WARNING"}
    config_path = write_config(tmp_path, config_dict)
    config = BrowserLauncherConfig(config_path)
    assert config.get_logging_level() == "WARNING"


def test_missing_config_file_raises():
    with pytest.raises(FileNotFoundError):
        BrowserLauncherConfig(Path("/nonexistent/path/config.toml"))


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
