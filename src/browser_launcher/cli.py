"""CLI interface for browser_launcher using Typer."""

import json
import logging
import sys
import termios
import tty
from importlib import resources
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import typer
from r3a_logger.logger import (  # type: ignore[import-untyped]
    get_current_logger,
    initialize_logging,
)
from rich.console import Console
from rich.panel import Panel

from browser_launcher.auth.factory import AuthFactory
from browser_launcher.auth.retry import AuthRetryHandler
from browser_launcher.browsers.factory import BrowserFactory
from browser_launcher.config import BrowserLauncherConfig
from browser_launcher.cookies import (
    CookieConfig,
    _dump_cookies_from_browser,
    inject_and_verify_cookies,
    read_cookies_from_browser,
    write_cookies_to_browser,
)
from browser_launcher.screenshot import IDGenerator, _capture_screenshot
from browser_launcher.utils import get_command_context

app = typer.Typer(help="Browser launcher CLI tool")
console = Console()

AUTH_CONFIG_FIELD_NAMES = {
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


def get_home_directory() -> Path:
    """Get the home directory path."""
    return Path.home() / ".browser_launcher"


def get_log_directory() -> Path:
    """Get the log directory path."""
    return get_home_directory() / "logs"


def create_config_template() -> str:
    """Create the content for the initial configuration file by reading
    from assets/default_config.toml.
    """
    with (
        resources.files("browser_launcher")
        .joinpath("assets/default_config.toml")
        .open("rb") as f
    ):
        return f.read().decode("utf-8")


def get_console_logging_setting() -> bool:
    """Read console_logging setting from config file, fallback to False on error."""
    try:
        config_loader = BrowserLauncherConfig()
        return config_loader.get_console_logging()
    except Exception:
        return False


def get_logging_level_setting() -> str:
    try:
        config_loader = BrowserLauncherConfig()
        return config_loader.get_logging_level()
    except Exception:
        return "WARNING"


def _setup_logging(
    verbose: bool = False,
    debug: bool = False,
    console_logging: bool = False,
    log_level: Optional[str] = None,
) -> None:
    """Adapter function to bridge old and new logging signatures.

    Args:
        verbose: Enable verbose logging (INFO level)
        debug: Enable debug logging (DEBUG level)
        console_logging: Enable console logging
        log_level: Optional explicit log level (overrides verbose/debug)
    """
    # Determine log level
    if log_level:
        pass  # Use provided log_level
    elif debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"

    # Get log directory
    log_dir = get_log_directory()

    # Call r3a_logger's initialize_logging with new signature
    initialize_logging(
        log_dir=log_dir,
        log_level=log_level,
        console_logging=console_logging,
        logger_name="browser_launcher",
        log_file_name=None,
    )


def _normalize_cookie_domain(domain: str) -> str:
    """Normalize a cookie domain by stripping leading dots.

    Browsers often return cookie domains with a leading dot (e.g.,
    ``.apple.com``), but the config stores them without (e.g.,
    ``apple.com``). This ensures consistent domain representation for
    cache lookups.

    Args:
        domain: The raw cookie domain string from the browser or config.

    Returns:
        The domain string with any leading dot removed.
    """
    return domain.lstrip(".") if domain else domain


def _resolve_cookie_domain(
    cookie_name: str,
    browser_domain: Optional[str],
    cookie_config_data: dict[str, Any],
    user: str,
    env: str,
) -> Optional[str]:
    """Resolve the correct domain for a cookie, preferring the config value.

    Looks up the cookie name in the ``[users.{user}.{env}.cookies]``
    configuration to find the authoritative domain.  If the cookie is not
    found in config, falls back to the normalised browser-reported domain.

    Args:
        cookie_name: The name of the cookie to resolve the domain for.
        browser_domain: The domain reported by the browser for this cookie.
        cookie_config_data: The full configuration data structure.
        user: The user identifier for config lookup.
        env: The environment name for config lookup.

    Returns:
        The resolved domain string, or ``None`` if no domain could be
        determined.
    """
    # Try config first (authoritative source)
    try:
        user_env_cookies = (
            cookie_config_data.get("users", {})
            .get(user, {})
            .get(env, {})
            .get("cookies", {})
        )
        if cookie_name in user_env_cookies:
            config_domain = user_env_cookies[cookie_name].get("domain")
            if config_domain:
                return _normalize_cookie_domain(config_domain)
    except (KeyError, TypeError, AttributeError):
        pass

    # Fall back to normalised browser domain
    if browser_domain:
        return _normalize_cookie_domain(browser_domain)

    return None


def cache_cookies_for_session(
    browser_controller: Any,
    user: str,
    env: str,
    domain: Optional[str],
    cookie_config_data: dict[str, Any],
    cookie_config: Optional[CookieConfig],
    logger: logging.Logger,
    console: Console,
) -> None:
    """Cache cookies from the active browser session for a given user and environment.

    This function reads cookies from the provided ``browser_controller`` for the
    domains configured under the given ``user`` and ``env`` in
    ``cookie_config_data``. Matching cookies are written to the cookie cache via
    ``cookie_config.update_cookie_cache`` and the updated configuration is
    persisted to the main ``config.toml`` file in the browser_launcher home
    directory.

    All exceptions raised while reading or persisting cookies are caught and
    logged; errors are also printed to the console. No exceptions are propagated
    to the caller.

    Args:
        browser_controller: An object wrapping the Selenium WebDriver instance
            whose ``driver`` attribute is used to read cookies from the browser.
        user: The user identifier whose cookie configuration and cache should be
            updated.
        env: The environment name (for example, ``"dev"``, ``"staging"`` or
            ``"prod"``) under which cookies are organized for the user.
        domain: The domain originally requested on the CLI. Used only for
            informational messages when no cookies are found.
        cookie_config_data: The full cookie configuration data structure loaded
            from ``config.toml``, used to determine which cookies and domains to
            target for caching.
        cookie_config: The ``CookieConfig`` instance used to update the cookie
            cache. If ``None``, the cache will not be updated and an error is
            logged and printed to the console.
        logger: The application logger used to record informational, debug, and
            error messages during the caching process.
        console: The Rich ``Console`` instance used to display user-facing
            messages about the caching operation.

    Returns:
        None. Results and any errors are communicated via logging and console
        output.
    """
    try:
        user_env_cookies = cookie_config_data["users"][user][env]["cookies"]
        target_cookies = list(user_env_cookies.keys())
        target_domains = list({val["domain"] for val in user_env_cookies.values()})
        browser_cookies: list[dict] = []
        target_browser_cookies: list[dict] = []
        for target_domain in target_domains:
            browser_cookies.extend(
                read_cookies_from_browser(browser_controller.driver, target_domain)
            )
        for cookie in browser_cookies:
            if cookie["name"] in target_cookies and cookie["name"] not in [
                c["name"] for c in target_browser_cookies
            ]:
                target_browser_cookies.append(cookie)

        logger.info(
            f"Read {len(target_browser_cookies)} cookies from browser for"
            f" {user}/{env}:{target_domains}"
        )
        if target_browser_cookies:
            if cookie_config is None:
                logger.error("CookieConfig is not initialized, cannot update cache")
                console.print(
                    "❌ [red]Error:[/red] CookieConfig is not initialized, "
                    "cannot update cache"
                )
                return
            # Update cache entries for each cookie
            for cookie in target_browser_cookies:
                cookie_config.update_cookie_cache(
                    user,
                    env,
                    user_env_cookies[cookie["name"]]["domain"],
                    cookie["name"],
                    cookie.get("value", ""),
                )

            # Save config back to file
            config_file = get_home_directory() / "config.toml"
            cookie_config.persist_to_file(config_file)

            console.print(
                f"✅ Cached {len(target_browser_cookies)} cookies for "
                f"{user}/{env}/{target_domains}"
            )
            logger.info(
                f"Saved {len(target_browser_cookies)} cookies "
                f"for {user}/{env}/{target_domains}"
            )

            users_json = json.dumps(cookie_config.config_data["users"], indent=2)
            logger.debug(f"Cookies: {users_json}")
        else:
            console.print(f"⚠️ No cookies found for domain {domain}")
            logger.debug(f"⚠️ No cookies found for domain {domain}")
    except Exception as e:
        console.print(f"❌ Error caching cookies: {e}")
        logger.error(f"Error caching cookies: {e}", exc_info=True)


def _persist_cookie_config(
    cookie_config: CookieConfig,
    logger: logging.Logger,
    console: Console,
) -> None:
    """Persist current cookie configuration to disk."""
    config_file = get_home_directory() / "config.toml"
    cookie_config.persist_to_file(config_file)
    logger.debug(f"Persisted cookie cache to {config_file}")
    console.print("✅ Saved authentication cookies to cache")


def _get_user_env_auth_modules(
    config_loader: BrowserLauncherConfig,
    user: str,
    env: str,
) -> list[str]:
    """Get configured auth modules in [users.{user}.{env}.auth]."""
    auth_section = (
        config_loader.config_data.get("users", {})
        .get(user, {})
        .get(env, {})
        .get("auth", {})
    )
    if not isinstance(auth_section, dict):
        return []

    return [
        key
        for key, value in auth_section.items()
        if isinstance(value, dict) and key not in AUTH_CONFIG_FIELD_NAMES
    ]


def _select_auth_module(
    config_loader: BrowserLauncherConfig,
    user: str,
    env: str,
) -> Optional[str]:
    """Select an auth module name from user/env scope first, then global scope."""
    logger = get_current_logger()
    if not logger:
        logger = logging.getLogger(__name__)
    logger.debug(f"Selecting authentication module for user={user}, env={env}")

    user_env_modules = _get_user_env_auth_modules(config_loader, user, env)
    if user_env_modules:
        selected = user_env_modules[0]
        logger.info(f"Selected auth module '{selected}' from user/env configuration")
        return selected

    configured_modules = config_loader.get_available_auth_modules()
    if configured_modules and len(configured_modules) > 0:
        selected = next(iter(configured_modules.keys()))
        logger.info(f"Selected auth module '{selected}' from global configuration")
        return selected

    logger.info("No authentication modules are configured in the config file.")
    return None


def _cache_auth_result_cookies(
    auth_cookies: list[dict[str, Any]],
    browser_controller: Any,
    cookie_config: CookieConfig,
    user: str,
    env: str,
    domain: Optional[str],
    logger: logging.Logger,
    console: Console,
) -> None:
    """Inject authenticated cookies into browser and persist cookie cache."""
    logger.info(f"Caching {len(auth_cookies)} authentication cookies")
    logger.debug(f"Cookie names: {[c.get('name') for c in auth_cookies]}")

    write_cookies_to_browser(browser_controller.driver, auth_cookies)
    logger.debug("Cookies written to browser")

    cached_count = 0
    for cookie in auth_cookies:
        cookie_name = cookie.get("name")
        raw_browser_domain = cookie.get("domain")

        # Resolve domain: prefer config-defined domain, then normalised
        # browser domain, then normalised launch-URL domain.
        cookie_domain = _resolve_cookie_domain(
            cookie_name=cookie_name or "",
            browser_domain=raw_browser_domain,
            cookie_config_data=cookie_config.config_data,
            user=user,
            env=env,
        )
        if not cookie_domain and domain:
            cookie_domain = _normalize_cookie_domain(domain)

        if not cookie_name or not cookie_domain:
            logger.warning(
                f"Skipping cookie with missing name or domain: "
                f"name={cookie_name}, domain={cookie_domain}"
            )
            continue

        if (
            raw_browser_domain
            and _normalize_cookie_domain(raw_browser_domain) != cookie_domain
        ):
            logger.info(
                f"Cookie '{cookie_name}' domain resolved from config: "
                f"browser='{raw_browser_domain}' -> config='{cookie_domain}'"
            )

        logger.debug(
            f"Updating cookie cache: {cookie_name} for {user}/{env}/{cookie_domain}"
        )
        cookie_config.update_cookie_cache(
            user,
            env,
            cookie_domain,
            cookie_name,
            cookie.get("value", ""),
        )
        cached_count += 1

    logger.info(f"Cached {cached_count} cookies to disk")
    _persist_cookie_config(cookie_config, logger, console)


def _run_authentication_attempt(
    authenticator: Any, launch_url: str
) -> list[dict[str, Any]]:
    """Run one authenticator attempt and return cookies on success."""
    logger = get_current_logger()
    if not logger:
        logger = logging.getLogger(__name__)
    logger.info(f"Running authentication attempt for URL: {launch_url}")
    logger.debug(f"Authenticator: {authenticator.__class__.__name__}")

    try:
        auth_result = authenticator.authenticate(launch_url)

        logger.debug(
            f"Authentication result: success={auth_result.success}, "
            f"cookies={auth_result.cookie_count}, "
            f"duration={auth_result.duration_seconds}s"
        )

        if not auth_result.success:
            error_msg = auth_result.error_message or "Authentication failed"
            logger.warning(f"Authentication failed: {error_msg}")
            raise RuntimeError(error_msg)

        if not auth_result.cookies:
            logger.warning("Authentication succeeded but returned no cookies")
            raise RuntimeError("Authentication returned no cookies")

        logger.info(
            f"Authentication successful: {auth_result.cookie_count} cookies obtained"
        )
        return auth_result.cookies

    except Exception as e:
        logger.error(
            f"Authentication attempt failed with {type(e).__name__}: {e}",
            exc_info=True,
        )
        raise


def attempt_authentication(  # noqa: C901
    browser_controller: Any,
    config_loader: BrowserLauncherConfig,
    cookie_config: CookieConfig,
    user: str,
    env: str,
    domain: Optional[str],
    launch_url: str,
    logger: logging.Logger,
    console: Console,
) -> Optional[list[dict[str, Any]]]:
    """Attempt authentication using cache first, then auth module with retries."""
    logger.info(f"Starting authentication attempt for {user}/{env}")
    logger.debug(f"Launch URL: {launch_url}, Domain: {domain}")

    # Try cached cookies first
    injected_cookies = inject_and_verify_cookies(
        browser_controller,
        user,
        env,
        cookie_config,
    )
    if injected_cookies:
        logger.info(
            f"Using {len(injected_cookies)} valid cached cookies for {user}/{env}"
        )
        return injected_cookies

    logger.debug("No valid cached cookies found, attempting fresh authentication")

    module_name = _select_auth_module(config_loader, user, env)
    if not module_name:
        logger.info("No authentication module configured; continuing without auth")
        return None

    logger.info(f"Attempting authentication with module '{module_name}'")

    try:
        auth_config = config_loader.get_auth_config(
            module_name=module_name,
            user=user,
            env=env,
        )
        logger.debug(
            f"Loaded auth config: timeout={auth_config.timeout_seconds}s, "
            f"retry={auth_config.retry_attempts}"
        )
    except Exception as e:
        logger.error(
            f"Failed to load auth config for '{module_name}': {e}", exc_info=True
        )
        logger.warning("Continuing without authentication due to config error")
        return None

    try:
        authenticator = AuthFactory.create(module_name, auth_config)
    except Exception as e:
        logger.error(
            f"Failed to create authenticator '{module_name}': {e}",
            exc_info=True,
        )
        logger.warning("Continuing without authentication due to creation error")
        return None

    if hasattr(authenticator, "setup_driver"):
        logger.debug("Setting up authenticator driver")
        authenticator.setup_driver(browser_controller.driver)

    # Create retry handler
    retry_handler = AuthRetryHandler(
        config=auth_config,
        console=console,
        logger=logger,
    )

    total_attempts = max(1, auth_config.retry_attempts + 1)
    logger.info(f"Starting authentication with up to {total_attempts} attempts")

    while retry_handler.current_attempt < total_attempts:
        retry_handler.increment_attempt()
        attempt = retry_handler.current_attempt

        logger.info(f"Authentication attempt {attempt}/{total_attempts}")

        try:
            auth_cookies = _run_authentication_attempt(authenticator, launch_url)
            _cache_auth_result_cookies(
                auth_cookies=auth_cookies,
                browser_controller=browser_controller,
                cookie_config=cookie_config,
                user=user,
                env=env,
                domain=domain,
                logger=logger,
                console=console,
            )
            logger.info(
                f"Authentication succeeded with module '{module_name}' "
                f"on attempt {attempt}/{total_attempts}"
            )
            return auth_cookies

        except Exception as e:
            error_msg = str(e)
            logger.warning(
                f"Authentication attempt {attempt}/{total_attempts} failed: {e}",
                exc_info=True,
            )

            # Check if we should retry
            if retry_handler.current_attempt >= total_attempts:
                logger.warning(
                    f"Maximum authentication attempts ({total_attempts}) reached"
                )
                break

            if not retry_handler.should_retry(error_message=error_msg):
                logger.info("User chose not to retry authentication")
                break

            # Update credentials if available
            if auth_config.credentials:
                logger.debug("Prompting for updated credentials")
                auth_config.credentials = retry_handler.prompt_for_credentials()

    logger.warning(
        "Authentication not completed; continuing without authenticated cookies"
    )
    return None


@app.command()
def init(
    force: bool = typer.Option(
        False, "--force", help="Force reinitialize even if directory exists"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable comprehensive debugging logs (DEBUG level, includes verbose)",
    ),
):
    """Initialize browser launcher by creating configuration directory and files.

    Logging Behavior:
    - Default: Clean console output, file logging only
    - --verbose: INFO level console logging for operational details
    - --debug: DEBUG level console logging including internal execution flow
    - File logging: Always active regardless of console flags
    """
    # Get the home directory where we'll add the config and logs
    home_dir = get_home_directory()
    home_dir_exists = home_dir.exists()

    # Log command execution
    context = get_command_context(
        "init", {"force": force, "verbose": verbose, "debug": debug}
    )
    console.print(f"Starting browser launcher initialization - {context}")

    if home_dir_exists and not force:
        console.print(
            f"📁 [yellow]Browser launcher directory already exists:[/yellow] {home_dir}"
        )
        console.print("[yellow]Use --force to reinitialize[/yellow]")
        return

    logger: Optional[logging.Logger] = None
    try:
        # Always read console_logging from config file
        console_logging = get_console_logging_setting()

        # Initialize logging first
        _setup_logging(verbose=verbose, debug=debug, console_logging=console_logging)
        logger = get_current_logger()
        if logger is None:
            raise RuntimeError("Logger was not initialized correctly.")

        # Log directory creation
        logger.debug(f"Creating home directory: {home_dir}")

        # Create directory
        if verbose:
            console.print(f"📁 Creating directory: {home_dir}")

        home_dir.mkdir(parents=True, exist_ok=True)

        # Create config file
        config_file = home_dir / "config.toml"
        logger.debug(f"Creating config file: {config_file}")

        if verbose:
            console.print(f"📝 Creating config file: {config_file}")

        config_content = create_config_template()
        config_file.write_text(config_content)

        # Create logs directory
        logs_dir = get_log_directory()
        logger.debug(f"Creating logs directory: {logs_dir}")

        if verbose:
            console.print(f"📁 Creating logs directory: {logs_dir}")

        logs_dir.mkdir(exist_ok=True)

        # Success message
        panel = Panel.fit(
            f"✅ Browser launcher initialized successfully!\n\n"
            f"📁 Configuration directory: {home_dir}\n"
            f"📝 Config file: {config_file}\n"
            f"📁 Logs directory: {logs_dir}\n\n"
            f"💡 Edit {config_file} to customize your settings.",
            title="🎉 Initialization Complete",
            border_style="green",
        )
        console.print(panel)

        # Log successful completion
        logger.info("Browser launcher initialization completed successfully")

    except PermissionError:
        error_msg = f"Permission denied: Cannot create directory {home_dir}"
        if logger:
            logger.error(error_msg)  # pragma: no cover
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        console.print(
            "💡 Try running with appropriate permissions or check directory access"
        )
        sys.exit(1)
    except Exception as e:
        error_msg = f"Failed to initialize: {e}"
        if logger:
            logger.error(error_msg, exc_info=True)  # pragma: no cover
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        sys.exit(1)


@app.command()
def launch(  # noqa: C901
    url: Optional[str] = typer.Argument(None, help="URL to open"),
    browser: Optional[str] = typer.Option(None, "--browser", help="Browser to use"),
    headless: bool = typer.Option(
        False, "--headless", help="Run browser in headless mode"
    ),
    user: str = typer.Option(
        "default",
        "--user",
        help="User profile for cookie and config lookup (default: 'default')",
    ),
    env: str = typer.Option(
        "prod",
        "--env",
        help="Environment for cookie and config lookup (default: 'prod')",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable comprehensive debugging logs (DEBUG level, includes verbose)",
    ),
    locale: str = typer.Option(
        "en-US",
        "--locale",
        help="Browser locale setting (default: 'en-US')",
    ),
):
    """Launch a browser with specified options.

    Logging Behavior:
    - Default: Clean console output, file logging only
    - --verbose: INFO level console logging for operational details
    - --debug: DEBUG level console logging including internal execution flow
    - File logging: Always active regardless of console flags

    Cookie Management:
    - --user: Selects user profile for hierarchical cookie lookup
    - --env: Selects environment for hierarchical cookie lookup
    - Cookies are injected after initial navigation if valid cache exists
    - See config documentation for hierarchical structure: [users.{user}.{env}.{domain}]
    """
    # Always read console_logging from config file
    console_logging = get_console_logging_setting()
    logging_level = get_logging_level_setting()

    # Initialize logging first
    _setup_logging(
        verbose=verbose,
        debug=debug,
        console_logging=console_logging,
        log_level=logging_level,
    )
    logger = get_current_logger()
    if logger is None:
        typer.echo("Logger was not initialized correctly.")
        raise typer.Exit(code=1)

    # Log command execution
    context = get_command_context(
        "launch",
        {
            "url": url,
            "browser": browser,
            "headless": headless,
            "user": user,
            "env": env,
            "verbose": verbose,
            "debug": debug,
        },
    )
    logger.info(f"Starting browser launch - {context}")

    # Load configuration
    try:
        config_loader = BrowserLauncherConfig()
    except FileNotFoundError as e:
        console.print(f"❌ [red]Error:[/red] {e}")
        logger.error(str(e))
        sys.exit(1)

    # Determine browser to use
    selected_browser = browser or config_loader.get_default_browser()
    if selected_browser not in BrowserFactory.get_available_browsers():
        console.print(f"❌ [red]Error:[/red] Unsupported browser: {selected_browser}")
        logger.error(f"Unsupported browser: {selected_browser}")
        sys.exit(1)

    # Get browser config
    try:
        browser_config = config_loader.get_browser_config(
            selected_browser, headless=headless
        )
    except Exception as e:
        console.print(f"❌ [red]Error loading browser config:[/red] {e}")
        logger.error(f"Error loading browser config: {e}")
        sys.exit(1)

    # Configure locale preferences if set
    if locale:
        browser_config.locale = locale
        logger.debug(f"Set browser locale to: {locale}")

    # Instantiate browser launcher
    try:
        browser_controller = BrowserFactory.create(
            selected_browser, browser_config, logger
        )
    except Exception as e:
        console.print(f"❌ [red]Error instantiating browser:[/red] {e}")
        logger.error(f"Error instantiating browser: {e}")
        sys.exit(1)

    # Determine URL
    launch_url = url or config_loader.get_default_url()
    console.print(f"🚀 Launching {selected_browser} at {launch_url}")
    logger.info(f"Launching {selected_browser} at {launch_url}")

    domain: Optional[str] = None  # Initialize domain variable for later use
    cookie_config_data: dict = {}  # Initialize cookie_config_data for later use
    cookie_config: Optional[CookieConfig] = (
        None  # Initialize cookie_config for later use
    )

    # Launch browser
    try:
        browser_controller.launch(url=launch_url)
    except Exception as e:
        console.print(f"❌ [red]Error launching browser:[/red] {e}")
        logger.error(f"Error launching browser: {e}")
        sys.exit(1)

    # Extract domain from URL for cookie injection
    try:
        parsed_url = urlparse(launch_url)
        domain = parsed_url.netloc or parsed_url.path.split("/")[0]
    except Exception as e:
        logger.warning(f"Could not extract domain from URL {launch_url}: {e}")
    # Continue execution even if domain extraction fails

    # Load cookie config and perform authentication flow (cache first)
    try:
        cookie_config_data = config_loader.config_data
        cookie_config = CookieConfig(cookie_config_data)

        logger.info(
            f"Attempting authentication for domain {domain} (user={user}, env={env})"
        )

        injected_cookies = attempt_authentication(
            browser_controller=browser_controller,
            config_loader=config_loader,
            cookie_config=cookie_config,
            user=user,
            env=env,
            domain=domain,
            launch_url=launch_url,
            logger=logger,
            console=console,
        )

        if injected_cookies:
            # Log and inform user of injected cookies
            console.print(
                f"✅ Applied {len(injected_cookies)} cookies: "
                f"{[cookie['name'] for cookie in injected_cookies]}"
            )

            if url:
                # TODO: improve config on this so that there is a 2 url pattern
                # 1 that matches domain for cookie injection
                # another that is the actual launch url
                # they could be same or different
                browser_controller.safe_get_address(url + "/ui")

    except Exception as e:
        logger.warning(
            f"Failed to inject/verify cookies for {domain}: {e}", exc_info=True
        )
        # Continue execution even if cookie injection fails

    # There are defaults already
    # app_name = "Demo"
    # screenshot_path = str(Path("~/Downloads").expanduser())
    gen = IDGenerator()

    # Wait for it to close
    # Try to set terminal to unbuffered mode for immediate character reading
    old_settings = None
    try:
        # Guard against non-TTY or closed stdin (e.g., during tests)
        if not sys.stdin.closed and sys.stdin.isatty():
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
            logger.debug("Terminal mode set to unbuffered (cbreak)")
        else:
            logger.debug(
                "stdin is not a TTY or is closed; skipping terminal mode configuration"
            )
    except (AttributeError, termios.error, OSError, ValueError) as e:
        logger.debug(f"Could not configure terminal mode: {type(e).__name__}: {e}")

    try:
        console.print("Press Ctrl+D or q to exit.")
        console.print("Press 'Enter' to capture a screenshot.")
        console.print("Press 's' to save/cache cookies for this session.")
        console.print("Press 'c' to dump all cookies from the browser.")

        # Skip interactive loop if stdin is not a usable TTY (e.g., during tests)

        while True:
            if browser_controller.driver.session_id is None:
                console.print(
                    "session has gone bad, you need to relaunch to be able to "
                    "capture screenshot"
                )
                break
            if sys.stdin.closed or not sys.stdin.isatty():
                logger.debug(
                    "Non-interactive environment detected; breaking out of input loop."
                )
                break
            try:
                char = sys.stdin.read(1)
            except ValueError as e:
                logger.debug(f"stdin closed or unavailable: {e}")
                break

            if not char or char == "\x04" or char.lower() == "q":
                break
            elif char.lower() == "\n" or char.lower() == "\r":
                try:
                    screenshot_name = gen.generate()
                    _capture_screenshot(
                        screenshot_name,
                        driver=browser_controller.driver,
                        delay=0.5,
                    )
                    console.print(f"Captured: {screenshot_name}")
                except Exception as e:
                    console.print(
                        "session has gone bad, you need to relaunch to be able"
                        f"to capture screenshot {type(e)} {e!r}"
                    )
                    raise e
            elif char.lower() == "s":
                cache_cookies_for_session(
                    browser_controller,
                    user,
                    env,
                    domain,
                    cookie_config_data,
                    cookie_config,
                    logger,
                    console,
                )
            elif char.lower() == "c":
                _dump_cookies_from_browser(browser_controller.driver, logger, console)

    except EOFError:
        console.print("\nExiting...")
    finally:
        # Restore original terminal settings if they were saved
        if old_settings is not None:
            try:
                if not sys.stdin.closed and sys.stdin.isatty():
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    logger.debug("Terminal mode restored")
            except (termios.error, OSError, ValueError) as e:
                logger.debug(
                    f"Could not restore terminal mode: {type(e).__name__}: {e}"
                )
        try:
            browser_controller.driver.close()
        except Exception:
            pass


@app.command()
def clean(  # noqa: C901
    force: bool = typer.Option(
        False, "--force", help="Force cleanup without confirmation"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable comprehensive debugging logs (DEBUG level, includes verbose)",
    ),
):
    """Clean up browser launcher by removing configuration directory and files.

    Logging Behavior:
    - Default: Clean console output, file logging only
    - --verbose: INFO level console logging for operational details
    - --debug: DEBUG level console logging including internal execution flow
    - File logging: Always active regardless of console flags
    """
    home_dir = get_home_directory()
    home_dir_exists = home_dir.exists()

    # Log command execution
    context = get_command_context(
        "clean", {"force": force, "verbose": verbose, "yes": yes, "debug": debug}
    )

    if verbose:
        console.print(f"Starting browser launcher cleanup : {context}")

    if not home_dir_exists:
        console.print(
            f"📁 [yellow]Browser launcher directory does not exist:[/yellow] {home_dir}"
        )
        console.print("💡 Nothing to clean up")
        return

    # Show what will be deleted
    if verbose:
        console.print("📂 Directory contents to be removed:")
        if home_dir.exists():
            for item in home_dir.rglob("*"):
                if item.is_file():
                    console.print(f"  📝 {item.relative_to(home_dir)}")
                elif item.is_dir():
                    console.print(f"  📁 {item.relative_to(home_dir)}/")

    # Confirmation prompt unless force or yes flag is used
    if not (force or yes):
        confirm = typer.confirm(
            f"Are you sure you want to delete {home_dir} and all its contents?",
            default=False,
        )
        if not confirm:
            console.print("🛑 Cleanup cancelled")
            return

    try:
        if verbose:
            console.print(f"🗑️ Removing directory: {home_dir}")

        # Remove directory and all contents
        import shutil

        shutil.rmtree(home_dir)

        # Success message
        panel = Panel.fit(
            f"✅ Browser launcher cleaned up successfully!\n\n"
            f"🗑️ Removed directory: {home_dir}\n\n"
            f"💡 Run 'browser-launcher init' to recreate the configuration.",
            title="🧹 Cleanup Complete",
            border_style="red",
        )
        console.print(panel)

        # Log successful completion
        console.print("Browser launcher cleanup completed successfully")

    except PermissionError:
        error_msg = f"Permission denied: Cannot remove directory {home_dir}"
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        console.print(
            "💡 Try running with appropriate permissions or check directory access"
        )
        sys.exit(1)
    except Exception as e:
        error_msg = f"Failed to clean up: {e}"
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    app()  # pragma: no cover
