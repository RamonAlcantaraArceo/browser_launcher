"""Unit tests for the DummyAuthenticator module."""

from datetime import datetime, timedelta

from browser_launcher.auth import AuthConfig, AuthResult, DummyAuthenticator


class TestDummyAuthenticator:
    """Test suite for DummyAuthenticator."""

    def test_initialization(self):
        """Test that DummyAuthenticator initializes correctly."""
        config = AuthConfig()
        authenticator = DummyAuthenticator(config)

        assert authenticator.config == config
        assert authenticator.driver is None
        assert authenticator.COOKIE_NAME == "DUMMY_SESSION"
        assert authenticator.COOKIE_EXPIRY_MINUTES == 5

    def test_authenticate_success(self):
        """Test successful authentication returns expected cookie."""
        config = AuthConfig(
            credentials={"username": "test_user"},
            custom_options={"auth_delay_seconds": 0},  # No delay for tests
        )
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        assert isinstance(result, AuthResult)
        assert result.success is True
        assert result.cookie_count == 1
        assert result.domain == "example.com"
        assert result.user == "test_user"
        assert result.error_message is None

        # Check cookie details
        cookie = result.cookies[0]
        assert cookie["name"] == "DUMMY_SESSION"
        assert len(cookie["value"]) > 0  # Random token
        assert cookie["domain"] == "example.com"
        assert cookie["path"] == "/"
        assert cookie["secure"] is True
        assert cookie["httpOnly"] is True
        assert cookie["sameSite"] == "Lax"
        assert "expiry" in cookie

    def test_authenticate_with_default_username(self):
        """Test authentication with no username defaults to 'test_user'."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        assert result.success is True
        assert result.user == "test_user"

    def test_authenticate_cookie_expiry(self):
        """Test that returned cookie has correct expiry time."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        before = datetime.now()
        result = authenticator.authenticate("https://example.com")
        after = datetime.now()

        cookie = result.cookies[0]
        expiry_timestamp = cookie["expiry"]
        expiry_datetime = datetime.fromtimestamp(expiry_timestamp)

        # Expiry should be approximately 5 minutes from now
        expected_min = before + timedelta(minutes=4, seconds=55)
        expected_max = after + timedelta(minutes=5, seconds=5)

        assert expected_min <= expiry_datetime <= expected_max

    def test_authenticate_with_url_variations(self):
        """Test authentication with different URL formats."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        # Test with full URL
        result = authenticator.authenticate("https://test.example.com/path")
        assert result.domain == "test.example.com"

        # Test with HTTP
        result = authenticator.authenticate("http://example.com")
        assert result.domain == "example.com"

        # Test with port
        result = authenticator.authenticate("https://example.com:8080/path")
        assert result.domain == "example.com:8080"

    def test_authenticate_duration_tracking(self):
        """Test that authentication duration is tracked correctly."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0.1})
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0.1
        assert result.duration_seconds < 1.0  # Should be quick

    def test_authenticate_session_data(self):
        """Test that session_data is populated correctly."""
        delay = 0.2
        config = AuthConfig(custom_options={"auth_delay_seconds": delay})
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        assert "authenticator" in result.session_data
        assert result.session_data["authenticator"] == "DummyAuthenticator"
        assert result.session_data["cookie_name"] == "DUMMY_SESSION"
        assert result.session_data["expiry_minutes"] == 5
        assert result.session_data["auth_delay"] == delay

    def test_authenticate_simulated_failure(self):
        """Test simulated authentication failure."""
        config = AuthConfig(
            credentials={"username": "test_user", "simulate_failure": True},
            custom_options={"auth_delay_seconds": 0},
        )
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        assert result.success is False
        assert result.cookie_count == 0
        assert result.error_message == "Simulated authentication failure for testing"
        assert result.domain == "example.com"
        assert result.user == "test_user"

    def test_authenticate_random_tokens(self):
        """Test that different authentication calls generate different tokens."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        result1 = authenticator.authenticate("https://example.com")
        result2 = authenticator.authenticate("https://example.com")

        token1 = result1.cookies[0]["value"]
        token2 = result2.cookies[0]["value"]

        assert token1 != token2  # Tokens should be random and unique

    def test_validate_config_success(self):
        """Test that validate_config accepts valid configurations."""
        config = AuthConfig()
        assert DummyAuthenticator.validate_config(config) is True

    def test_validate_config_with_custom_delay(self):
        """Test configuration validation with custom auth delay."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 1.5})
        assert DummyAuthenticator.validate_config(config) is True

    def test_validate_config_with_invalid_delay(self):
        """Test configuration validation with invalid auth delay."""
        config = AuthConfig(custom_options={"auth_delay_seconds": -1})
        assert DummyAuthenticator.validate_config(config) is False

        config = AuthConfig(custom_options={"auth_delay_seconds": "invalid"})
        assert DummyAuthenticator.validate_config(config) is False

    def test_cleanup(self):
        """Test cleanup method."""
        config = AuthConfig()
        authenticator = DummyAuthenticator(config)

        # Cleanup should not raise any errors
        authenticator.cleanup()
        assert authenticator.driver is None

    def test_get_cookie_by_name(self):
        """Test retrieving specific cookie from result."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")

        session_cookie = result.get_cookie_by_name("DUMMY_SESSION")
        assert session_cookie is not None
        assert session_cookie["name"] == "DUMMY_SESSION"

        missing_cookie = result.get_cookie_by_name("NONEXISTENT")
        assert missing_cookie is None

    def test_result_to_dict(self):
        """Test converting AuthResult to dictionary."""
        config = AuthConfig(
            credentials={"username": "test_user"},
            custom_options={"auth_delay_seconds": 0},
        )
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["domain"] == "example.com"
        assert result_dict["user"] == "test_user"
        assert result_dict["cookie_count"] == 1
        assert "timestamp" in result_dict
        assert "cookies" in result_dict

    def test_multiple_credentials_formats(self):
        """Test authentication with various credential formats."""
        # Test with username only
        config1 = AuthConfig(credentials={"username": "alice"})
        result1 = DummyAuthenticator(config1).authenticate("https://example.com")
        assert result1.success is True
        assert result1.user == "alice"

        # Test with username and password (password ignored for dummy auth)
        config2 = AuthConfig(credentials={"username": "bob", "password": "secret"})
        result2 = DummyAuthenticator(config2).authenticate("https://example.com")
        assert result2.success is True
        assert result2.user == "bob"

        # Test with extra fields (ignored)
        config3 = AuthConfig(
            credentials={"username": "charlie", "api_key": "12345", "extra": "data"}
        )
        result3 = DummyAuthenticator(config3).authenticate("https://example.com")
        assert result3.success is True
        assert result3.user == "charlie"

    def test_cookie_format_compatibility(self):
        """Test that returned cookies match Selenium's expected format."""
        config = AuthConfig(custom_options={"auth_delay_seconds": 0})
        authenticator = DummyAuthenticator(config)

        result = authenticator.authenticate("https://example.com")
        cookie = result.cookies[0]

        # Check all required fields for Selenium compatibility
        required_fields = ["name", "value", "domain", "path"]
        for field in required_fields:
            assert field in cookie
            assert cookie[field] is not None

        # Check optional fields are present with appropriate types
        assert isinstance(cookie.get("secure"), bool)
        assert isinstance(cookie.get("httpOnly"), bool)
        assert cookie.get("sameSite") in ["Strict", "Lax", "None", None]
        assert isinstance(cookie.get("expiry"), int)
