"""Form-based authentication module for browser_launcher.

This example authenticator demonstrates how to implement a custom
authentication module using Selenium to interact with a login form.
It navigates to a login page, fills in username/password fields,
submits the form, and extracts cookies from the authenticated session.

Configuration Requirements:
    The following credentials must be provided via ``AuthConfig.credentials``:

    - ``username`` (str): The username or email to enter.
    - ``password`` (str): The password to enter.

    Optional ``AuthConfig.custom_options``:

    - ``login_url`` (str): Override URL for the login page.
      Defaults to the ``url`` argument passed to ``authenticate()``.
    - ``username_field`` (str): CSS selector for the username input.
      Defaults to ``"input[name='username'], input[type='email'], #username"``.
    - ``password_field`` (str): CSS selector for the password input.
      Defaults to ``"input[name='password'], input[type='password'], #password"``.
    - ``submit_button`` (str): CSS selector for the submit button.
      Defaults to ``"button[type='submit'], input[type='submit'], #login-button"``.
    - ``success_indicator`` (str): CSS selector for an element that appears
      only after successful login (e.g. a dashboard header or user menu).
      If not set, success is determined by cookie presence alone.
    - ``pre_login_delay`` (float): Seconds to wait after page load
      before interacting with the form. Defaults to ``0.5``.
    - ``post_login_delay`` (float): Seconds to wait after form
      submission for cookies to settle. Defaults to ``1.0``.

Cookie Return Format:
    On success the ``AuthResult.cookies`` list contains dictionaries in
    Selenium's cookie format::

        {
            "name": "<cookie_name>",
            "value": "<cookie_value>",
            "domain": ".example.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "sameSite": "Lax",
            "expiry": 1740700000     # Unix timestamp
        }

    If ``AuthConfig.required_cookies`` is set, only those cookies are
    returned; otherwise **all** cookies from the browser session are
    included.

Entry Point Registration (pyproject.toml):
    .. code-block:: toml

        [tool.poetry.plugins."browser_launcher.authenticators"]
        form_auth = "examples.auth_modules.form_auth:FormAuthenticator"

Usage Example:
    .. code-block:: python

        from browser_launcher.auth.config import AuthConfig
        from examples.auth_modules.form_auth import FormAuthenticator

        config = AuthConfig(
            timeout_seconds=45,
            credentials={"username": "alice@example.com", "password": "s3cret"},
            custom_options={
                "username_field": "#email",
                "password_field": "#passwd",
                "submit_button": "button.login-btn",
                "success_indicator": ".dashboard-header",
            },
            required_cookies=["session_id", "auth_token"],
        )

        authenticator = FormAuthenticator(config)
        # Optionally attach a pre-existing Selenium WebDriver:
        # authenticator.setup_driver(driver)
        result = authenticator.authenticate("https://example.com/login")

        if result.success:
            for cookie in result.cookies:
                print(f"{cookie['name']}={cookie['value']}")
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from browser_launcher.auth.base import AuthenticatorBase
from browser_launcher.auth.config import AuthConfig
from browser_launcher.auth.exceptions import (
    AuthConfigError,
    AuthenticationFailedError,
    AuthTimeoutError,
    CredentialsError,
)
from browser_launcher.auth.result import AuthResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
#  Default CSS selectors  (each string is a comma-separated group selector)
# ---------------------------------------------------------------------------
_DEFAULT_USERNAME_SELECTOR = (
    "input[name='username'], input[type='email'], input#username"
)
_DEFAULT_PASSWORD_SELECTOR = (
    "input[name='password'], input[type='password'], input#password"
)
_DEFAULT_SUBMIT_SELECTOR = (
    "button[type='submit'], input[type='submit'], button#login-button"
)


class FormAuthenticator(AuthenticatorBase):
    """Browser-based form authentication module.

    Uses Selenium to navigate to a login page, fill in credentials,
    submit the form, and extract session cookies from the authenticated
    browser session.

    This class is intended as a **reference implementation** that covers
    the most common "username + password" form login pattern.  For more
    complex flows (CAPTCHA, MFA, OAuth redirects, etc.) extend this
    class or write a new authenticator from scratch using
    ``AuthenticatorBase``.
    """

    def __init__(self, config: AuthConfig) -> None:
        """Initialize the form authenticator.

        Args:
            config: AuthConfig instance with authentication settings.

        Raises:
            AuthConfigError: If required configuration is missing or invalid.
        """
        logger.info("Initializing FormAuthenticator")
        super().__init__(config)

        # Resolve custom options with sensible defaults
        opts = config.custom_options
        self._username_selector: str = opts.get(
            "username_field", _DEFAULT_USERNAME_SELECTOR
        )
        self._password_selector: str = opts.get(
            "password_field", _DEFAULT_PASSWORD_SELECTOR
        )
        self._submit_selector: str = opts.get("submit_button", _DEFAULT_SUBMIT_SELECTOR)
        self._success_indicator: Optional[str] = opts.get("success_indicator")
        self._pre_login_delay: float = float(opts.get("pre_login_delay", 0.5))
        self._post_login_delay: float = float(opts.get("post_login_delay", 1.0))
        self._login_url_override: Optional[str] = opts.get("login_url")

        logger.debug(
            "FormAuthenticator selectors — "
            f"username: {self._username_selector!r}, "
            f"password: {self._password_selector!r}, "
            f"submit: {self._submit_selector!r}, "
            f"success_indicator: {self._success_indicator!r}"
        )
        logger.info("FormAuthenticator initialized successfully")

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def authenticate(self, url: str, **kwargs: Any) -> AuthResult:
        """Perform form-based authentication.

        Navigates to the login URL, fills in the username and password
        fields, clicks the submit button, and waits for the login to
        complete.  Cookies are then extracted from the browser session.

        If ``self.driver`` is ``None`` an ``AuthConfigError`` is raised
        because form authentication requires a browser.

        Args:
            url: The target URL to authenticate against.  If a
                ``login_url`` custom option is set it takes precedence.
            **kwargs: Reserved for future use.

        Returns:
            AuthResult containing the extracted cookies.

        Raises:
            AuthConfigError: If no WebDriver is attached.
            CredentialsError: If username or password is missing.
            AuthTimeoutError: When page load or element waits exceed the
                configured timeout.
            AuthenticationFailedError: When the form submission does not
                result in expected cookies or success indicator.
        """
        start_time = time.time()
        login_url = self._login_url_override or url
        domain = self._extract_domain(login_url)

        logger.info(f"Starting form authentication for {login_url}")

        # --- Validate pre-conditions -----------------------------------
        if self.driver is None:
            raise AuthConfigError(
                "No WebDriver attached",
                details=(
                    "FormAuthenticator requires a browser.  "
                    "Call setup_driver(driver) before authenticate()."
                ),
            )

        username = self._get_validated_credentials()
        password = self.config.get_credential("password")
        # password is guaranteed non-empty by _get_validated_credentials
        assert password is not None

        logger.debug(f"Authenticating user: {username}")

        # --- Navigate to login page ------------------------------------
        try:
            self._navigate_to_login(login_url)
        except TimeoutException as exc:
            duration = time.time() - start_time
            self.take_failure_screenshot("form_auth_page_load_timeout")
            raise AuthTimeoutError(
                "Login page load timed out",
                details=f"Timed out loading {login_url} after {duration:.1f}s",
            ) from exc
        except WebDriverException as exc:
            duration = time.time() - start_time
            self.take_failure_screenshot("form_auth_navigation_error")
            raise AuthenticationFailedError(
                "Failed to navigate to login page",
                details=str(exc),
            ) from exc

        # --- Fill and submit the form ----------------------------------
        try:
            self._fill_and_submit(username, password)
        except NoSuchElementException as exc:
            self.take_failure_screenshot("form_auth_element_not_found")
            raise AuthenticationFailedError(
                "Login form element not found",
                details=(
                    f"Could not locate form element.  "
                    f"Check selectors: username={self._username_selector!r}, "
                    f"password={self._password_selector!r}, "
                    f"submit={self._submit_selector!r}.  Error: {exc}"
                ),
            ) from exc
        except TimeoutException as exc:
            duration = time.time() - start_time
            self.take_failure_screenshot("form_auth_element_timeout")
            raise AuthTimeoutError(
                "Timed out waiting for form elements",
                details=(
                    "Could not find form elements within "
                    f"{self.config.element_wait_timeout}s"
                ),
            ) from exc

        # --- Wait for authentication to complete -----------------------
        try:
            self._wait_for_login_complete()
        except TimeoutException as exc:
            duration = time.time() - start_time
            self.take_failure_screenshot("form_auth_login_timeout")
            raise AuthTimeoutError(
                "Authentication did not complete in time",
                details=(
                    f"Waited {self.config.timeout_seconds}s for login to complete."
                ),
            ) from exc

        # --- Extract cookies ------------------------------------------
        cookies = self._extract_cookies(domain)
        duration = time.time() - start_time

        if not cookies:
            self.take_failure_screenshot("form_auth_no_cookies")
            raise AuthenticationFailedError(
                "No cookies obtained after login",
                details=(
                    "Form submission succeeded but no matching cookies "
                    "were found in the browser session."
                ),
            )

        # --- Validate required cookies --------------------------------
        cookie_names = [c["name"] for c in cookies]
        if not self.config.validate_required_cookies(cookie_names):
            missing = [n for n in self.config.required_cookies if n not in cookie_names]
            self.take_failure_screenshot("form_auth_missing_cookies")
            raise AuthenticationFailedError(
                "Required cookies missing",
                details=f"Missing: {missing}.  Got: {cookie_names}",
            )

        result = AuthResult(
            cookies=cookies,
            success=True,
            timestamp=datetime.now(),
            domain=domain,
            user=username,
            session_data={
                "authenticator": self.__class__.__name__,
                "login_url": login_url,
                "cookie_count": len(cookies),
            },
            duration_seconds=duration,
        )

        logger.info(
            f"Form authentication completed in {duration:.2f}s — "
            f"{result.cookie_count} cookie(s) for '{domain}'"
        )
        return result

    # ------------------------------------------------------------------
    #  Configuration validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_config(cls, config: AuthConfig) -> bool:
        """Validate configuration for form authentication.

        Checks that credentials contain ``username`` and ``password``
        and that custom option values are sensible.

        Args:
            config: AuthConfig to validate.

        Returns:
            True if the configuration is valid, False otherwise.
        """
        logger.debug(f"Validating configuration for {cls.__name__}")

        if not super().validate_config(config):
            logger.warning(f"Parent validation failed for {cls.__name__}")
            return False

        # Require credentials
        if not config.get_credential("username"):
            logger.warning("FormAuthenticator requires 'username' in credentials")
            return False
        if not config.get_credential("password"):
            logger.warning("FormAuthenticator requires 'password' in credentials")
            return False

        # Validate optional numeric custom_options
        for key in ("pre_login_delay", "post_login_delay"):
            raw = config.custom_options.get(key)
            if raw is not None:
                try:
                    val = float(raw)
                    if val < 0:
                        logger.warning(f"Invalid {key}: must be >= 0, got {val}")
                        return False
                except (TypeError, ValueError):
                    logger.warning(f"Invalid {key}: expected number, got {raw!r}")
                    return False

        logger.debug(f"Configuration validated successfully for {cls.__name__}")
        return True

    # ------------------------------------------------------------------
    #  Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Clean up form authenticator resources.

        Resets internal state.  The WebDriver itself is **not** quit —
        that responsibility lies with the caller / browser launcher.
        """
        logger.debug(f"Cleaning up {self.__class__.__name__} resources")
        super().cleanup()
        logger.info(f"{self.__class__.__name__} cleanup completed")

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _get_validated_credentials(self) -> str:
        """Validate and return the username from config credentials.

        Also validates that a password is present.

        Returns:
            The username string.

        Raises:
            CredentialsError: If username or password is missing.
        """
        username = self.config.get_credential("username")
        password = self.config.get_credential("password")

        if not username:
            raise CredentialsError(
                "Missing username",
                details="Provide 'username' in AuthConfig.credentials.",
            )
        if not password:
            raise CredentialsError(
                "Missing password",
                details="Provide 'password' in AuthConfig.credentials.",
            )
        return username

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract the domain (netloc) from a URL.

        Args:
            url: URL string.

        Returns:
            Domain portion of the URL; falls back to ``"localhost"``
            if parsing fails.
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            logger.debug(f"Extracted domain: {domain}")
            return domain
        except Exception as exc:
            logger.warning(f"Failed to parse URL '{url}': {exc}")
            return "localhost"

    def _navigate_to_login(self, login_url: str) -> None:
        """Navigate to the login page and wait for readiness.

        Args:
            login_url: Full URL of the login page.

        Raises:
            TimeoutException: If the page does not load within the
                configured ``page_load_timeout``.
            WebDriverException: On other Selenium navigation errors.
        """
        assert self.driver is not None
        logger.debug(f"Navigating to login page: {login_url}")
        self.driver.get(login_url)

        if self._pre_login_delay > 0:
            logger.debug(f"Waiting {self._pre_login_delay}s for page to settle")
            time.sleep(self._pre_login_delay)

        logger.debug("Login page loaded")

    def _find_element_by_css_group(
        self, css_group: str, wait: Optional[WebDriverWait] = None
    ) -> Any:
        """Find the first element matching any selector in a comma-separated CSS group.

        When a ``WebDriverWait`` is provided, the method uses an explicit
        wait with ``visibility_of_element_located`` for each selector.
        Otherwise it falls back to a simple ``find_element``.

        Args:
            css_group: Comma-separated CSS selectors.
            wait: Optional ``WebDriverWait`` instance for explicit waits.

        Returns:
            The first matching ``WebElement``.

        Raises:
            NoSuchElementException: If no selector matches.
        """
        assert self.driver is not None
        selectors = [s.strip() for s in css_group.split(",")]
        last_exc: Optional[Exception] = None

        for selector in selectors:
            try:
                if wait is not None:
                    element = wait.until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                logger.debug(f"Found element with selector: {selector!r}")
                return element
            except (NoSuchElementException, TimeoutException) as exc:
                last_exc = exc
                logger.debug(f"Selector {selector!r} did not match")

        # Preserve the original exception type so the caller can
        # distinguish between "not found" and "timed out".
        if isinstance(last_exc, TimeoutException):
            raise TimeoutException(
                f"Timed out waiting for selectors: {selectors}"
            ) from last_exc
        raise NoSuchElementException(
            f"None of the selectors matched: {selectors}"
        ) from last_exc

    def _fill_and_submit(self, username: str, password: str) -> None:
        """Locate login form fields, fill credentials, and submit.

        Args:
            username: Value for the username field.
            password: Value for the password field.

        Raises:
            NoSuchElementException: If a required form element cannot be
                found.
            TimeoutException: If waiting for an element exceeds the
                configured ``element_wait_timeout``.
        """
        assert self.driver is not None

        wait = WebDriverWait(self.driver, self.config.element_wait_timeout)

        # Username
        logger.debug("Locating username field")
        username_el = self._find_element_by_css_group(self._username_selector, wait)
        username_el.clear()
        username_el.send_keys(username)
        logger.debug("Username entered")

        # Password
        logger.debug("Locating password field")
        password_el = self._find_element_by_css_group(self._password_selector, wait)
        password_el.clear()
        password_el.send_keys(password)
        logger.debug("Password entered")

        # Submit
        logger.debug("Locating submit button")
        submit_el = self._find_element_by_css_group(self._submit_selector, wait)
        submit_el.click()
        logger.info("Login form submitted")

    def _wait_for_login_complete(self) -> None:
        """Wait for the login flow to finish after form submission.

        If a ``success_indicator`` CSS selector is configured, the method
        waits for that element to appear.  Otherwise it simply waits for
        the ``post_login_delay`` period.

        Raises:
            TimeoutException: If the success indicator does not appear
                within ``timeout_seconds``.
        """
        assert self.driver is not None

        if self._success_indicator:
            logger.debug(f"Waiting for success indicator: {self._success_indicator!r}")
            WebDriverWait(self.driver, self.config.timeout_seconds).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, self._success_indicator)
                )
            )
            logger.debug("Success indicator found")
        elif self._post_login_delay > 0:
            logger.debug(f"Waiting {self._post_login_delay}s after form submission")
            time.sleep(self._post_login_delay)

    def _extract_cookies(self, domain: str) -> List[Dict[str, Any]]:
        """Extract cookies from the current browser session.

        If ``AuthConfig.required_cookies`` is non-empty, only those
        cookies are returned.  Otherwise all cookies are included.

        Args:
            domain: The domain used for authentication (for logging).

        Returns:
            List of cookie dictionaries in Selenium format.
        """
        assert self.driver is not None

        all_cookies: List[Dict[str, Any]] = self.driver.get_cookies()
        logger.debug(f"Browser has {len(all_cookies)} cookie(s) after login")

        if self.config.required_cookies:
            required_set = set(self.config.required_cookies)
            filtered = [c for c in all_cookies if c.get("name") in required_set]
            logger.debug(
                f"Filtered to {len(filtered)} required cookie(s) "
                f"out of {len(all_cookies)}"
            )
            return filtered

        return all_cookies
