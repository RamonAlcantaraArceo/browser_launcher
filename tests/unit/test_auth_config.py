"""Unit tests for the AuthConfig dataclass."""

from pathlib import Path

import pytest

from browser_launcher.auth.config import AuthConfig

# ---------------------------------------------------------------------------
#  Construction & defaults
# ---------------------------------------------------------------------------


class TestAuthConfigDefaults:
    """Tests for AuthConfig default values."""

    def test_default_values(self):
        """AuthConfig should have sensible defaults."""
        config = AuthConfig()

        assert config.timeout_seconds == 30
        assert config.retry_attempts == 1
        assert config.retry_delay_seconds == 1.0
        assert config.headless is True
        assert config.credentials == {}
        assert config.custom_options == {}
        assert config.user_agent is None
        assert config.window_size == (1920, 1080)
        assert config.page_load_timeout == 20
        assert config.element_wait_timeout == 10
        assert config.screenshot_on_failure is False
        assert config.screenshot_directory is None
        assert config.allowed_domains == []
        assert config.required_cookies == []

    def test_custom_values(self):
        """AuthConfig should accept all custom keyword arguments."""
        config = AuthConfig(
            timeout_seconds=60,
            retry_attempts=5,
            retry_delay_seconds=2.5,
            headless=False,
            credentials={"username": "alice"},
            custom_options={"foo": "bar"},
            user_agent="CustomAgent/1.0",
            window_size=(800, 600),
            page_load_timeout=45,
            element_wait_timeout=15,
            screenshot_on_failure=True,
            screenshot_directory="/tmp/screenshots",
            allowed_domains=["example.com"],
            required_cookies=["session_id"],
        )

        assert config.timeout_seconds == 60
        assert config.retry_attempts == 5
        assert config.retry_delay_seconds == 2.5
        assert config.headless is False
        assert config.credentials == {"username": "alice"}
        assert config.custom_options == {"foo": "bar"}
        assert config.user_agent == "CustomAgent/1.0"
        assert config.window_size == (800, 600)
        assert config.page_load_timeout == 45
        assert config.element_wait_timeout == 15
        assert config.screenshot_on_failure is True
        assert isinstance(config.screenshot_directory, Path)
        assert config.allowed_domains == ["example.com"]
        assert config.required_cookies == ["session_id"]


# ---------------------------------------------------------------------------
#  __post_init__ validation
# ---------------------------------------------------------------------------


class TestAuthConfigValidation:
    """Tests for AuthConfig __post_init__ validation."""

    def test_invalid_timeout_zero(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            AuthConfig(timeout_seconds=0)

    def test_invalid_timeout_negative(self):
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            AuthConfig(timeout_seconds=-5)

    def test_invalid_retry_attempts_negative(self):
        with pytest.raises(ValueError, match="retry_attempts cannot be negative"):
            AuthConfig(retry_attempts=-1)

    def test_retry_attempts_zero_is_valid(self):
        """Zero retries is valid — means no retries, one attempt only."""
        config = AuthConfig(retry_attempts=0)
        assert config.retry_attempts == 0

    def test_invalid_retry_delay_negative(self):
        with pytest.raises(ValueError, match="retry_delay_seconds cannot be negative"):
            AuthConfig(retry_delay_seconds=-0.1)

    def test_retry_delay_zero_is_valid(self):
        config = AuthConfig(retry_delay_seconds=0)
        assert config.retry_delay_seconds == 0

    def test_invalid_page_load_timeout(self):
        with pytest.raises(ValueError, match="page_load_timeout must be positive"):
            AuthConfig(page_load_timeout=0)

    def test_invalid_element_wait_timeout(self):
        with pytest.raises(ValueError, match="element_wait_timeout must be positive"):
            AuthConfig(element_wait_timeout=-1)

    def test_invalid_window_size_single_value(self):
        with pytest.raises(ValueError, match="window_size"):
            AuthConfig(window_size=(0, 600))

    def test_invalid_window_size_negative(self):
        with pytest.raises(ValueError, match="window_size"):
            AuthConfig(window_size=(-1, -1))

    def test_screenshot_directory_string_converted_to_path(self):
        config = AuthConfig(screenshot_directory="/tmp/shots")
        assert isinstance(config.screenshot_directory, Path)
        assert str(config.screenshot_directory) == "/tmp/shots"

    def test_screenshot_directory_path_stays_path(self):
        p = Path("/tmp/shots")
        config = AuthConfig(screenshot_directory=p)
        assert config.screenshot_directory is p


# ---------------------------------------------------------------------------
#  get_credential / set_credential
# ---------------------------------------------------------------------------


class TestAuthConfigCredentials:
    """Tests for credential access helpers."""

    def test_get_credential_returns_value(self):
        config = AuthConfig(credentials={"username": "alice", "token": "abc"})
        assert config.get_credential("username") == "alice"
        assert config.get_credential("token") == "abc"

    def test_get_credential_returns_default(self):
        config = AuthConfig()
        assert config.get_credential("missing") is None
        assert config.get_credential("missing", "fallback") == "fallback"

    def test_set_credential(self):
        config = AuthConfig()
        config.set_credential("username", "bob")
        assert config.credentials["username"] == "bob"

    def test_set_credential_overwrites_existing(self):
        config = AuthConfig(credentials={"username": "alice"})
        config.set_credential("username", "bob")
        assert config.get_credential("username") == "bob"


# ---------------------------------------------------------------------------
#  validate_required_cookies
# ---------------------------------------------------------------------------


class TestValidateRequiredCookies:
    """Tests for validate_required_cookies method."""

    def test_no_required_cookies(self):
        """When no required cookies are configured, validation always passes."""
        config = AuthConfig()
        assert config.validate_required_cookies([]) is True
        assert config.validate_required_cookies(["any"]) is True

    def test_all_present(self):
        config = AuthConfig(required_cookies=["a", "b"])
        assert config.validate_required_cookies(["a", "b", "c"]) is True

    def test_some_missing(self):
        config = AuthConfig(required_cookies=["a", "b", "c"])
        assert config.validate_required_cookies(["a"]) is False

    def test_none_present(self):
        config = AuthConfig(required_cookies=["x"])
        assert config.validate_required_cookies([]) is False


# ---------------------------------------------------------------------------
#  to_dict
# ---------------------------------------------------------------------------


class TestAuthConfigToDict:
    """Tests for to_dict serialization."""

    def test_roundtrip_keys(self):
        config = AuthConfig(
            credentials={"u": "v"},
            allowed_domains=["example.com"],
            required_cookies=["sid"],
        )
        d = config.to_dict()

        expected_keys = {
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
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_returns_copies(self):
        """Mutating the dict should not affect the original config."""
        config = AuthConfig(credentials={"k": "v"})
        d = config.to_dict()
        d["credentials"]["k"] = "changed"
        assert config.credentials["k"] == "v"

    def test_screenshot_directory_serialized_as_string(self):
        config = AuthConfig(screenshot_directory="/tmp/shots")
        d = config.to_dict()
        assert d["screenshot_directory"] == "/tmp/shots"

    def test_screenshot_directory_none(self):
        config = AuthConfig()
        d = config.to_dict()
        assert d["screenshot_directory"] is None
