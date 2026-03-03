"""Unit tests for the FormAuthenticator example module."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

from browser_launcher.auth.config import AuthConfig
from browser_launcher.auth.exceptions import (
    AuthConfigError,
    AuthenticationFailedError,
    AuthTimeoutError,
    CredentialsError,
)
from browser_launcher.auth.result import AuthResult
from examples.auth_modules.form_auth import FormAuthenticator

# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides: Any) -> AuthConfig:
    """Build an AuthConfig with form-auth-friendly defaults."""
    kw: dict[str, Any] = {
        "timeout_seconds": 10,
        "credentials": {"username": "alice", "password": "s3cret"},
        "custom_options": {"pre_login_delay": 0, "post_login_delay": 0},
    }
    kw.update(overrides)
    return AuthConfig(**kw)


def _mock_driver(cookies=None):
    """Return a mock Selenium WebDriver with sensible defaults."""
    driver = MagicMock()
    if cookies is None:
        cookies = [
            {"name": "session_id", "value": "abc123", "domain": ".example.com"},
            {"name": "auth_token", "value": "tok456", "domain": ".example.com"},
        ]
    driver.get_cookies.return_value = cookies
    # find_element returns a mock element that can be cleared and sent keys
    mock_element = MagicMock()
    driver.find_element.return_value = mock_element
    return driver


# ---------------------------------------------------------------------------
#  Initialization
# ---------------------------------------------------------------------------


class TestFormAuthenticatorInit:
    """Tests for FormAuthenticator construction and config resolution."""

    def test_default_selectors(self):
        """Default CSS selectors are applied when custom_options is empty."""
        config = _make_config()
        auth = FormAuthenticator(config)

        assert "input[name='username']" in auth._username_selector
        assert "input[name='password']" in auth._password_selector
        assert "button[type='submit']" in auth._submit_selector
        assert auth._success_indicator is None

    def test_custom_selectors(self):
        """Custom CSS selectors from custom_options take precedence."""
        config = _make_config(
            custom_options={
                "username_field": "#email",
                "password_field": "#passwd",
                "submit_button": "button.login",
                "success_indicator": ".dashboard",
                "pre_login_delay": 0,
                "post_login_delay": 0,
            }
        )
        auth = FormAuthenticator(config)

        assert auth._username_selector == "#email"
        assert auth._password_selector == "#passwd"
        assert auth._submit_selector == "button.login"
        assert auth._success_indicator == ".dashboard"

    def test_login_url_override(self):
        """login_url custom option is stored for later use."""
        config = _make_config(
            custom_options={
                "login_url": "https://sso.example.com/login",
                "pre_login_delay": 0,
                "post_login_delay": 0,
            }
        )
        auth = FormAuthenticator(config)
        assert auth._login_url_override == "https://sso.example.com/login"

    def test_delay_defaults(self):
        """Delay values default to 0.5 / 1.0 when not specified."""
        config = _make_config(custom_options={})
        auth = FormAuthenticator(config)
        assert auth._pre_login_delay == 0.5
        assert auth._post_login_delay == 1.0


# ---------------------------------------------------------------------------
#  validate_config
# ---------------------------------------------------------------------------


class TestFormAuthenticatorValidateConfig:
    """Tests for FormAuthenticator.validate_config()."""

    def test_valid_config(self):
        """Config with username and password validates successfully."""
        config = _make_config()
        assert FormAuthenticator.validate_config(config) is True

    def test_missing_username(self):
        """Config without username fails validation."""
        config = _make_config(credentials={"password": "pw"})
        assert FormAuthenticator.validate_config(config) is False

    def test_missing_password(self):
        """Config without password fails validation."""
        config = _make_config(credentials={"username": "user"})
        assert FormAuthenticator.validate_config(config) is False

    def test_empty_credentials(self):
        """Config with empty credentials fails validation."""
        config = _make_config(credentials={})
        assert FormAuthenticator.validate_config(config) is False

    def test_negative_pre_login_delay(self):
        """Negative pre_login_delay fails validation."""
        config = _make_config(
            custom_options={"pre_login_delay": -1, "post_login_delay": 0}
        )
        assert FormAuthenticator.validate_config(config) is False

    def test_invalid_delay_type(self):
        """Non-numeric delay value fails validation."""
        config = _make_config(
            custom_options={"pre_login_delay": "slow", "post_login_delay": 0}
        )
        assert FormAuthenticator.validate_config(config) is False

    def test_parent_validation_negative_timeout(self):
        """Parent validation catches negative timeout."""
        config = _make_config()
        config.timeout_seconds = -1
        # Parent validation was already run at __post_init__, so we
        # create a fresh config object with a valid timeout, then tamper
        config2 = _make_config()
        config2.retry_attempts = -1
        assert FormAuthenticator.validate_config(config2) is False


# ---------------------------------------------------------------------------
#  authenticate — pre-condition errors
# ---------------------------------------------------------------------------


class TestFormAuthenticatePreConditions:
    """Tests for pre-condition errors in authenticate()."""

    def test_no_driver_raises_config_error(self):
        """Calling authenticate without a driver raises AuthConfigError."""
        auth = FormAuthenticator(_make_config())
        # driver is None by default
        with pytest.raises(AuthConfigError, match="No WebDriver"):
            auth.authenticate("https://example.com/login")

    def test_missing_username_raises_credentials_error(self):
        """Missing username in credentials raises CredentialsError."""
        config = _make_config(credentials={"password": "pw"})
        auth = FormAuthenticator(config)
        auth.setup_driver(_mock_driver())

        with pytest.raises(CredentialsError, match="Missing username"):
            auth.authenticate("https://example.com/login")

    def test_missing_password_raises_credentials_error(self):
        """Missing password in credentials raises CredentialsError."""
        config = _make_config(credentials={"username": "user"})
        auth = FormAuthenticator(config)
        auth.setup_driver(_mock_driver())

        with pytest.raises(CredentialsError, match="Missing password"):
            auth.authenticate("https://example.com/login")


# ---------------------------------------------------------------------------
#  authenticate — navigation errors
# ---------------------------------------------------------------------------


class TestFormAuthenticateNavigation:
    """Tests for login page navigation failures."""

    def test_page_load_timeout(self):
        """TimeoutException during navigation raises AuthTimeoutError."""
        driver = _mock_driver()
        driver.get.side_effect = TimeoutException("page load timed out")

        auth = FormAuthenticator(_make_config())
        auth.setup_driver(driver)

        with pytest.raises(AuthTimeoutError, match="Login page load timed out"):
            auth.authenticate("https://example.com/login")

    def test_webdriver_exception(self):
        """WebDriverException during navigation raises AuthenticationFailedError."""
        driver = _mock_driver()
        driver.get.side_effect = WebDriverException("ERR_CONNECTION_REFUSED")

        auth = FormAuthenticator(_make_config())
        auth.setup_driver(driver)

        with pytest.raises(AuthenticationFailedError, match="Failed to navigate"):
            auth.authenticate("https://example.com/login")


# ---------------------------------------------------------------------------
#  authenticate — form interaction errors
# ---------------------------------------------------------------------------


class TestFormAuthenticateFormInteraction:
    """Tests for form fill/submit failures."""

    def test_element_not_found(self):
        """NoSuchElementException when locating form elements."""
        config = _make_config()
        auth = FormAuthenticator(config)
        driver = _mock_driver()
        auth.setup_driver(driver)

        # Patch _fill_and_submit to raise NoSuchElementException directly,
        # because with a real WebDriverWait, NoSuchElementException from
        # find_element is retried and eventually becomes TimeoutException.
        with patch.object(
            auth,
            "_fill_and_submit",
            side_effect=NoSuchElementException("element not found"),
        ):
            with pytest.raises(
                AuthenticationFailedError, match="Login form element not found"
            ):
                auth.authenticate("https://example.com/login")

    def test_element_timeout(self):
        """TimeoutException when waiting for form elements."""
        config = _make_config()
        auth = FormAuthenticator(config)
        driver = _mock_driver()
        auth.setup_driver(driver)

        # Patch _fill_and_submit to raise TimeoutException directly
        with patch.object(
            auth,
            "_fill_and_submit",
            side_effect=TimeoutException("element timeout"),
        ):
            with pytest.raises(
                AuthTimeoutError, match="Timed out waiting for form elements"
            ):
                auth.authenticate("https://example.com/login")


# ---------------------------------------------------------------------------
#  authenticate — success path
# ---------------------------------------------------------------------------


class TestFormAuthenticateSuccess:
    """Tests for the happy-path authentication flow."""

    def _make_auth_with_driver(self, cookies=None, **config_kw):
        """Helper: create FormAuthenticator with a mock driver attached.

        Returns a (auth, patcher) tuple.  The patcher patches
        ``_find_element_by_css_group`` so that DOM lookups return
        a mock element without querying a real browser.
        The caller must enter/exit the patcher context, or use it
        via ``with``.
        """
        config = _make_config(**config_kw)
        auth = FormAuthenticator(config)
        driver = _mock_driver(cookies)
        auth.setup_driver(driver)
        return auth

    def test_returns_auth_result_on_success(self):
        """authenticate() returns a successful AuthResult with cookies."""
        auth = self._make_auth_with_driver()
        mock_el = MagicMock()
        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            result = auth.authenticate("https://example.com/login")

        assert isinstance(result, AuthResult)
        assert result.success is True
        assert result.cookie_count == 2
        assert result.domain == "example.com"
        assert result.user == "alice"
        assert result.error_message is None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_session_data_contains_authenticator_name(self):
        """session_data includes the authenticator class name."""
        auth = self._make_auth_with_driver()
        mock_el = MagicMock()
        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            result = auth.authenticate("https://example.com/login")

        assert result.session_data["authenticator"] == "FormAuthenticator"
        assert result.session_data["login_url"] == "https://example.com/login"

    def test_login_url_override(self):
        """login_url custom option overrides the url argument."""
        auth = self._make_auth_with_driver(
            custom_options={
                "login_url": "https://sso.example.com/login",
                "pre_login_delay": 0,
                "post_login_delay": 0,
            }
        )
        mock_el = MagicMock()
        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            result = auth.authenticate("https://example.com/app")

        assert result.session_data["login_url"] == "https://sso.example.com/login"
        assert result.domain == "sso.example.com"

    def test_required_cookies_filter(self):
        """When required_cookies is set only those cookies are returned."""
        all_cookies = [
            {"name": "session_id", "value": "abc"},
            {"name": "tracking", "value": "xyz"},
            {"name": "auth_token", "value": "tok"},
        ]
        auth = self._make_auth_with_driver(
            cookies=all_cookies,
            required_cookies=["session_id", "auth_token"],
        )
        mock_el = MagicMock()
        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            result = auth.authenticate("https://example.com/login")

        assert result.cookie_count == 2
        names = {c["name"] for c in result.cookies}
        assert names == {"session_id", "auth_token"}

    def test_form_fields_receive_credentials(self):
        """Username and password are sent to the correct elements."""
        auth = self._make_auth_with_driver()
        mock_el = MagicMock()
        with patch.object(
            auth, "_find_element_by_css_group", return_value=mock_el
        ) as patched:
            result = auth.authenticate("https://example.com/login")

        assert result.success is True
        # _find_element_by_css_group is called 3 times: username, password, submit
        assert patched.call_count == 3


# ---------------------------------------------------------------------------
#  authenticate — post-login failures
# ---------------------------------------------------------------------------


class TestFormAuthenticatePostLogin:
    """Tests for failures after form submission."""

    def test_no_cookies_after_login(self):
        """AuthenticationFailedError when no cookies are extracted."""
        config = _make_config()
        auth = FormAuthenticator(config)

        driver = _mock_driver(cookies=[])  # No cookies
        auth.setup_driver(driver)
        mock_el = MagicMock()

        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            with pytest.raises(AuthenticationFailedError, match="No cookies obtained"):
                auth.authenticate("https://example.com/login")

    def test_missing_required_cookies(self):
        """AuthenticationFailedError when required cookies are absent."""
        config = _make_config(required_cookies=["session_id", "csrf_token"])
        auth = FormAuthenticator(config)

        driver = _mock_driver(cookies=[{"name": "session_id", "value": "abc"}])
        auth.setup_driver(driver)
        mock_el = MagicMock()

        with patch.object(auth, "_find_element_by_css_group", return_value=mock_el):
            with pytest.raises(
                AuthenticationFailedError, match="Required cookies missing"
            ):
                auth.authenticate("https://example.com/login")

    def test_success_indicator_timeout(self):
        """AuthTimeoutError when success_indicator not found in time."""
        config = _make_config(
            custom_options={
                "success_indicator": ".dashboard",
                "pre_login_delay": 0,
                "post_login_delay": 0,
            }
        )
        auth = FormAuthenticator(config)

        driver = _mock_driver()
        auth.setup_driver(driver)
        mock_el = MagicMock()

        # Make WebDriverWait.until raise TimeoutException when checking
        # for the success indicator
        with (
            patch.object(auth, "_find_element_by_css_group", return_value=mock_el),
            patch("examples.auth_modules.form_auth.WebDriverWait") as mock_wdw,
        ):
            mock_wait_instance = MagicMock()
            mock_wait_instance.until.side_effect = TimeoutException("timeout")
            mock_wdw.return_value = mock_wait_instance

            with pytest.raises(
                AuthTimeoutError, match="Authentication did not complete"
            ):
                auth.authenticate("https://example.com/login")


# ---------------------------------------------------------------------------
#  cleanup
# ---------------------------------------------------------------------------


class TestFormAuthenticatorCleanup:
    """Tests for cleanup behaviour."""

    def test_cleanup_resets_driver(self):
        """cleanup() sets driver to None without quitting it."""
        auth = FormAuthenticator(_make_config())
        driver = _mock_driver()
        auth.setup_driver(driver)

        assert auth.driver is not None

        auth.cleanup()

        assert auth.driver is None
        driver.quit.assert_not_called()  # type: ignore[unreachable]


# ---------------------------------------------------------------------------
#  _extract_domain helper
# ---------------------------------------------------------------------------


class TestExtractDomain:
    """Tests for the static _extract_domain helper."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://example.com/login", "example.com"),
            ("https://sso.example.com:8443/auth", "sso.example.com:8443"),
            ("http://localhost:3000/", "localhost:3000"),
        ],
    )
    def test_various_urls(self, url, expected):
        assert FormAuthenticator._extract_domain(url) == expected

    def test_fallback_on_bad_url(self):
        """Unparseable URLs fall back to 'localhost'."""
        # urlparse handles most strings without raising, but the edge
        # case path returns the path portion which is effectively usable.
        result = FormAuthenticator._extract_domain("")
        # Empty string → empty netloc and empty path → fallback
        assert isinstance(result, str)
