"""Unit tests for the AuthFactory class."""

from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

from browser_launcher.auth.base import AuthenticatorBase
from browser_launcher.auth.config import AuthConfig
from browser_launcher.auth.exceptions import AuthConfigError, AuthError
from browser_launcher.auth.factory import AuthFactory
from browser_launcher.auth.result import AuthResult

# ---------------------------------------------------------------------------
#  Helpers — concrete subclass used for testing
# ---------------------------------------------------------------------------


class _StubAuthenticator(AuthenticatorBase):
    """Minimal concrete authenticator for factory tests."""

    MODULE_NAME: ClassVar[str] = "stub"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def authenticate(self, url: str) -> AuthResult:
        return AuthResult(success=True, cookies=[])

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


class _BadValidationAuth(AuthenticatorBase):
    """Authenticator whose validate_config always returns False."""

    MODULE_NAME: ClassVar[str] = "bad_val"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def authenticate(self, url: str) -> AuthResult:
        return AuthResult(success=True, cookies=[])

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return False


class _ErrorOnInit(AuthenticatorBase):
    """Authenticator that blows up in __init__."""

    MODULE_NAME: ClassVar[str] = "error_init"
    REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

    def __init__(self, config: AuthConfig) -> None:
        raise RuntimeError("boom")

    def authenticate(self, url: str) -> AuthResult:
        return AuthResult(success=True, cookies=[])

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        return True


# ---------------------------------------------------------------------------
#  Helpers — mock entry points
# ---------------------------------------------------------------------------


def _make_entry_point(name: str, cls: type) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = cls
    return ep


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_factory_cache():
    """Ensure every test starts with a clean cache."""
    AuthFactory.clear_cache()
    yield
    AuthFactory.clear_cache()


@pytest.fixture()
def default_config() -> AuthConfig:
    return AuthConfig()


# ---------------------------------------------------------------------------
#  discover_modules
# ---------------------------------------------------------------------------


class TestDiscoverModules:
    """Tests for AuthFactory.discover_modules."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_discovers_valid_module(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        result = AuthFactory.discover_modules()
        assert "stub" in result
        assert result["stub"] is _StubAuthenticator

    @patch("browser_launcher.auth.factory.entry_points")
    def test_skips_non_subclass(self, mock_ep):
        """Entry points that don't extend AuthenticatorBase are skipped."""

        class _NotAuth:
            pass

        mock_ep.return_value = [_make_entry_point("bad", _NotAuth)]
        result = AuthFactory.discover_modules()
        assert result == {}

    @patch("browser_launcher.auth.factory.entry_points")
    def test_skips_abstract_base(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("base", AuthenticatorBase)]
        result = AuthFactory.discover_modules()
        assert result == {}

    @patch("browser_launcher.auth.factory.entry_points")
    def test_skips_entry_point_load_failure(self, mock_ep):
        """If loading an entry point raises, it's skipped."""
        bad_ep = MagicMock()
        bad_ep.name = "broken"
        bad_ep.load.side_effect = ImportError("no module")
        mock_ep.return_value = [bad_ep]
        result = AuthFactory.discover_modules()
        assert result == {}

    @patch("browser_launcher.auth.factory.entry_points")
    def test_uses_cache_on_second_call(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        AuthFactory.discover_modules()
        AuthFactory.discover_modules()
        mock_ep.assert_called_once()

    @patch("browser_launcher.auth.factory.entry_points")
    def test_refresh_cache_forces_rediscovery(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        AuthFactory.discover_modules()
        AuthFactory.discover_modules(refresh_cache=True)
        assert mock_ep.call_count == 2

    @patch("browser_launcher.auth.factory.entry_points")
    def test_returns_copy_of_cache(self, mock_ep):
        """Mutating the returned dict should not affect the cache."""
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        result = AuthFactory.discover_modules()
        result.pop("stub")
        assert "stub" in AuthFactory.discover_modules()

    @patch("browser_launcher.auth.factory.entry_points")
    def test_entry_points_exception_raises_auth_error(self, mock_ep):
        mock_ep.side_effect = RuntimeError("discovery kaboom")
        with pytest.raises(AuthError, match="Failed to discover"):
            AuthFactory.discover_modules()

    @patch("browser_launcher.auth.factory.entry_points")
    def test_discovers_multiple_modules(self, mock_ep):
        mock_ep.return_value = [
            _make_entry_point("stub", _StubAuthenticator),
            _make_entry_point("bad_val", _BadValidationAuth),
        ]
        result = AuthFactory.discover_modules()
        assert set(result.keys()) == {"stub", "bad_val"}


# ---------------------------------------------------------------------------
#  get_available_modules
# ---------------------------------------------------------------------------


class TestGetAvailableModules:
    """Tests for AuthFactory.get_available_modules."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_returns_list_of_names(self, mock_ep):
        mock_ep.return_value = [
            _make_entry_point("a", _StubAuthenticator),
            _make_entry_point("b", _BadValidationAuth),
        ]
        names = AuthFactory.get_available_modules()
        assert sorted(names) == ["a", "b"]

    @patch("browser_launcher.auth.factory.entry_points")
    def test_empty_when_no_modules(self, mock_ep):
        mock_ep.return_value = []
        assert AuthFactory.get_available_modules() == []


# ---------------------------------------------------------------------------
#  create
# ---------------------------------------------------------------------------


class TestCreate:
    """Tests for AuthFactory.create."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_happy_path(self, mock_ep, default_config):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        auth = AuthFactory.create("stub", default_config)
        assert isinstance(auth, _StubAuthenticator)

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_unknown_module_raises(self, mock_ep, default_config):
        mock_ep.return_value = []
        with pytest.raises(AuthConfigError, match="not found"):
            AuthFactory.create("nonexistent", default_config)

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_validation_failure_raises(self, mock_ep, default_config):
        mock_ep.return_value = [_make_entry_point("bad_val", _BadValidationAuth)]
        with pytest.raises(AuthConfigError, match="Invalid configuration"):
            AuthFactory.create("bad_val", default_config)

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_skip_validation(self, mock_ep, default_config):
        """When validate_config=False, skip validation even though it would fail."""
        mock_ep.return_value = [_make_entry_point("bad_val", _BadValidationAuth)]
        auth = AuthFactory.create("bad_val", default_config, validate_config=False)
        assert isinstance(auth, _BadValidationAuth)

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_init_error_raises(self, mock_ep, default_config):
        mock_ep.return_value = [_make_entry_point("err", _ErrorOnInit)]
        with pytest.raises(AuthError, match="Failed to create"):
            AuthFactory.create("err", default_config)

    @patch("browser_launcher.auth.factory.entry_points")
    def test_create_uses_module_cache(self, mock_ep, default_config):
        """Second create for same module should hit module cache."""
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        AuthFactory.create("stub", default_config)
        AuthFactory.create("stub", default_config)
        # entry_points called once (discovery cached) and entry_point.load called once
        mock_ep.assert_called_once()


# ---------------------------------------------------------------------------
#  validate_module_config
# ---------------------------------------------------------------------------


class TestValidateModuleConfig:
    """Tests for AuthFactory.validate_module_config."""

    def test_custom_validate_returns_true(self, default_config):
        assert AuthFactory.validate_module_config(_StubAuthenticator, default_config)

    def test_custom_validate_returns_false(self, default_config):
        assert not AuthFactory.validate_module_config(
            _BadValidationAuth, default_config
        )

    def test_validate_config_exception_returns_false(self, default_config):
        """If validate_config raises, treat as invalid."""

        class _Boom(AuthenticatorBase):
            MODULE_NAME: ClassVar[str] = "boom"
            REQUIRED_CREDENTIALS: ClassVar[list[str]] = []

            def authenticate(self, url: str) -> AuthResult:
                return AuthResult(success=True, cookies=[])

            @classmethod
            def validate_config(cls, config: AuthConfig) -> bool:
                raise RuntimeError("validate boom")

        assert not AuthFactory.validate_module_config(_Boom, default_config)


# ---------------------------------------------------------------------------
#  get_module_info
# ---------------------------------------------------------------------------


class TestGetModuleInfo:
    """Tests for AuthFactory.get_module_info."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_returns_info_dict(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        info = AuthFactory.get_module_info("stub")
        assert info is not None
        assert info["name"] == "stub"
        assert info["class"] == "_StubAuthenticator"
        assert "has_custom_validation" in info

    @patch("browser_launcher.auth.factory.entry_points")
    def test_returns_none_for_unknown(self, mock_ep):
        mock_ep.return_value = []
        assert AuthFactory.get_module_info("nope") is None


# ---------------------------------------------------------------------------
#  clear_cache
# ---------------------------------------------------------------------------


class TestClearCache:
    """Tests for AuthFactory.clear_cache."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_clear_resets_discovery_cache(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        AuthFactory.discover_modules()
        AuthFactory.clear_cache()
        # Next call should re-discover
        AuthFactory.discover_modules()
        assert mock_ep.call_count == 2

    @patch("browser_launcher.auth.factory.entry_points")
    def test_clear_resets_module_cache(self, mock_ep, default_config):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        AuthFactory.create("stub", default_config)
        AuthFactory.clear_cache()
        assert AuthFactory._module_cache == {}
        assert AuthFactory._discovery_cache is None


# ---------------------------------------------------------------------------
#  is_module_available
# ---------------------------------------------------------------------------


class TestIsModuleAvailable:
    """Tests for AuthFactory.is_module_available."""

    @patch("browser_launcher.auth.factory.entry_points")
    def test_true_for_known_module(self, mock_ep):
        mock_ep.return_value = [_make_entry_point("stub", _StubAuthenticator)]
        assert AuthFactory.is_module_available("stub") is True

    @patch("browser_launcher.auth.factory.entry_points")
    def test_false_for_unknown_module(self, mock_ep):
        mock_ep.return_value = []
        assert AuthFactory.is_module_available("nope") is False

    @patch("browser_launcher.auth.factory.entry_points")
    def test_false_on_discovery_error(self, mock_ep):
        mock_ep.side_effect = RuntimeError("kaboom")
        assert AuthFactory.is_module_available("any") is False
