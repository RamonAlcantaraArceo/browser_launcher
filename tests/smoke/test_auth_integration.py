"""Smoke / integration tests for the authentication subsystem.

These tests exercise the interactions between AuthFactory, AuthConfig,
AuthRetryHandler, and the CLI's attempt_authentication function to ensure
the full auth pipeline works end-to-end (with Selenium mocked out).
"""

import logging
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from browser_launcher.auth.base import AuthenticatorBase
from browser_launcher.auth.config import AuthConfig
from browser_launcher.auth.factory import AuthFactory
from browser_launcher.auth.result import AuthResult
from browser_launcher.auth.retry import AuthRetryHandler

# ---------------------------------------------------------------------------
#  Helpers — lightweight authenticator stubs
# ---------------------------------------------------------------------------


class _SuccessAuth(AuthenticatorBase):
    """Authenticator that always succeeds with predictable cookies."""

    MODULE_NAME: ClassVar[str] = "success"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def authenticate(self, url: str, **kwargs) -> AuthResult:
        return AuthResult(
            success=True,
            cookies=[{"name": "session", "value": "abc123", "domain": "example.com"}],
        )

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


class _FailAuth(AuthenticatorBase):
    """Authenticator that always fails."""

    MODULE_NAME: ClassVar[str] = "fail"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def authenticate(self, url: str, **kwargs) -> AuthResult:
        return AuthResult(
            success=False,
            cookies=[],
            error_message="invalid credentials",
        )

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


class _ErrorAuth(AuthenticatorBase):
    """Authenticator that always raises."""

    MODULE_NAME: ClassVar[str] = "error"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def authenticate(self, url: str, **kwargs) -> AuthResult:
        raise RuntimeError("selenium kaboom")

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


class _NeedsCredsAuth(AuthenticatorBase):
    """Authenticator that requires username and password."""

    MODULE_NAME: ClassVar[str] = "needs_creds"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = ["username", "password"]

    def authenticate(self, url: str, **kwargs) -> AuthResult:
        u = self.config.get_credential("username")
        p = self.config.get_credential("password")
        if u == "admin" and p == "secret":
            return AuthResult(
                success=True,
                cookies=[{"name": "token", "value": "tok123", "domain": "a.com"}],
            )
        return AuthResult(success=False, cookies=[], error_message="bad creds")

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------


def _make_ep(name: str, cls: type) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = cls
    return ep


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear():
    AuthFactory.clear_cache()
    yield
    AuthFactory.clear_cache()


# ---------------------------------------------------------------------------
#  Factory ↔ Authenticator integration
# ---------------------------------------------------------------------------


class TestFactoryAuthenticatorIntegration:
    """End-to-end: discover → create → authenticate."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_discover_create_authenticate(self, mock_ep):
        """Full happy-path pipeline through the factory."""
        mock_ep.return_value = [_make_ep("success", _SuccessAuth)]
        config = AuthConfig()

        # discover
        available = AuthFactory.get_available_modules()
        assert "success" in available

        # create
        auth = AuthFactory.create("success", config)
        assert isinstance(auth, _SuccessAuth)

        # authenticate
        result = auth.authenticate("https://example.com")
        assert result.success is True
        assert result.cookie_count == 1
        cookie = result.get_cookie_by_name("session")
        assert cookie is not None
        assert cookie["value"] == "abc123"

    @patch("browser_launcher.auth.factory.entry_points")
    def test_discover_create_authenticate_fail(self, mock_ep):
        mock_ep.return_value = [_make_ep("fail", _FailAuth)]
        auth = AuthFactory.create("fail", AuthConfig())
        result = auth.authenticate("https://example.com")
        assert result.success is False
        assert result.error_message == "invalid credentials"

    @patch("browser_launcher.auth.factory.entry_points")
    def test_factory_skips_invalid_and_uses_valid(self, mock_ep):
        """Mix of valid and invalid entry points."""

        class _NotAuth:
            pass

        mock_ep.return_value = [
            _make_ep("bad", _NotAuth),
            _make_ep("good", _SuccessAuth),
        ]
        modules = AuthFactory.discover_modules()
        assert "bad" not in modules
        assert "good" in modules


# ---------------------------------------------------------------------------
#  Config ↔ Authenticator integration
# ---------------------------------------------------------------------------


@pytest.mark.smoke
class TestConfigAuthenticatorIntegration:
    """Auth config values flow correctly through to authenticators."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_credentials_available_in_authenticator(self, mock_ep):
        mock_ep.return_value = [_make_ep("needs_creds", _NeedsCredsAuth)]
        config = AuthConfig(credentials={"username": "admin", "password": "secret"})
        auth = AuthFactory.create("needs_creds", config)
        result = auth.authenticate("https://a.com")
        assert result.success is True

    @patch("browser_launcher.auth.factory.entry_points")
    def test_wrong_credentials_fail(self, mock_ep):
        mock_ep.return_value = [_make_ep("needs_creds", _NeedsCredsAuth)]
        config = AuthConfig(credentials={"username": "wrong", "password": "wrong"})
        auth = AuthFactory.create("needs_creds", config)
        result = auth.authenticate("https://a.com")
        assert result.success is False


# ---------------------------------------------------------------------------
#  Retry handler integration
# ---------------------------------------------------------------------------


class TestRetryHandlerIntegration:
    """AuthRetryHandler integration with real config and console/logger."""

    def test_retry_handler_respects_config_attempts(self):
        config = AuthConfig(retry_attempts=2)
        handler = AuthRetryHandler(
            config=config,
            console=MagicMock(),
            logger=logging.getLogger("test"),
        )
        # remaining = retry_attempts + 1 (initial) - current_attempt (0) = 3
        assert handler.get_remaining_attempts() == 3
        handler.increment_attempt()
        assert handler.get_remaining_attempts() == 2

    @patch("browser_launcher.auth.factory.entry_points")
    def test_retry_loop_with_eventual_success(self, mock_ep):
        """Simulate a retry loop: first attempt fails, second succeeds."""
        mock_ep.return_value = [_make_ep("success", _SuccessAuth)]
        config = AuthConfig(retry_attempts=2)
        auth = AuthFactory.create("success", config)

        handler = AuthRetryHandler(
            config=config,
            console=MagicMock(),
            logger=logging.getLogger("test"),
        )

        attempt = 0
        results: list[AuthResult] = []
        total_attempts = config.retry_attempts + 1

        while handler.current_attempt < total_attempts:
            handler.increment_attempt()
            attempt += 1
            if attempt == 1:
                # simulate failure
                results.append(
                    AuthResult(
                        success=False, cookies=[], error_message="transient error"
                    )
                )
            else:
                results.append(auth.authenticate("https://example.com"))
                if results[-1].success:
                    break

        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True


# ---------------------------------------------------------------------------
#  AuthResult integration
# ---------------------------------------------------------------------------


class TestAuthResultIntegration:
    """Verify AuthResult serialization round-trips and cookie access."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_result_to_dict_and_back(self, mock_ep):
        mock_ep.return_value = [_make_ep("success", _SuccessAuth)]
        auth = AuthFactory.create("success", AuthConfig())
        result = auth.authenticate("https://example.com")

        d = result.to_dict()
        assert d["success"] is True
        assert isinstance(d["cookies"], list)
        assert d["cookie_count"] == 1

    @patch("browser_launcher.auth.factory.entry_points")
    def test_get_cookie_by_name_returns_none_for_missing(self, mock_ep):
        mock_ep.return_value = [_make_ep("success", _SuccessAuth)]
        auth = AuthFactory.create("success", AuthConfig())
        result = auth.authenticate("https://example.com")
        assert result.get_cookie_by_name("nonexistent") is None


# ---------------------------------------------------------------------------
#  CLI attempt_authentication (mocked factory + driver)
# ---------------------------------------------------------------------------


class TestAttemptAuthenticationSmoke:
    """Smoke tests for the CLI's attempt_authentication orchestrator."""

    @patch("browser_launcher.auth.factory.entry_points")
    @patch("browser_launcher.cli.inject_and_verify_cookies", return_value=None)
    @patch("browser_launcher.cli._select_auth_module", return_value="success")
    def test_fresh_auth_succeeds(self, mock_select, mock_inject, mock_ep):
        """When no cached cookies, fresh auth succeeds and returns cookies."""
        from rich.console import Console

        from browser_launcher.cli import attempt_authentication
        from browser_launcher.config import BrowserLauncherConfig

        mock_ep.return_value = [_make_ep("success", _SuccessAuth)]
        AuthFactory.clear_cache()

        browser_ctrl = MagicMock()
        config_loader = MagicMock(spec=BrowserLauncherConfig)
        config_loader.get_auth_config.return_value = AuthConfig()

        cookie_config = MagicMock()
        logger = logging.getLogger("smoke_test")
        console = Console(quiet=True)

        result = attempt_authentication(
            browser_controller=browser_ctrl,
            config_loader=config_loader,
            cookie_config=cookie_config,
            user="alice",
            env="staging",
            domain="example.com",
            launch_url="https://example.com/login",
            logger=logger,
            console=console,
        )

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "session"

    @patch("browser_launcher.cli.inject_and_verify_cookies")
    def test_cached_cookies_short_circuit(self, mock_inject):
        """If cached cookies exist, skip auth entirely."""
        from rich.console import Console

        from browser_launcher.cli import attempt_authentication
        from browser_launcher.config import BrowserLauncherConfig

        cached = [{"name": "cached", "value": "abc"}]
        mock_inject.return_value = cached

        browser_ctrl = MagicMock()
        config_loader = MagicMock(spec=BrowserLauncherConfig)
        cookie_config = MagicMock()
        logger = logging.getLogger("smoke_test")
        console = Console(quiet=True)

        result = attempt_authentication(
            browser_controller=browser_ctrl,
            config_loader=config_loader,
            cookie_config=cookie_config,
            user="bob",
            env="prod",
            domain=None,
            launch_url="https://example.com",
            logger=logger,
            console=console,
        )

        assert result == cached

    @patch("browser_launcher.cli.inject_and_verify_cookies", return_value=None)
    @patch("browser_launcher.cli._select_auth_module", return_value=None)
    def test_no_auth_module_returns_none(self, mock_select, mock_inject):
        """When no auth module is configured, return None gracefully."""
        from rich.console import Console

        from browser_launcher.cli import attempt_authentication
        from browser_launcher.config import BrowserLauncherConfig

        result = attempt_authentication(
            browser_controller=MagicMock(),
            config_loader=MagicMock(spec=BrowserLauncherConfig),
            cookie_config=MagicMock(),
            user="u",
            env="e",
            domain=None,
            launch_url="https://example.com",
            logger=logging.getLogger("test"),
            console=Console(quiet=True),
        )

        assert result is None
