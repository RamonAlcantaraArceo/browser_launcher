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

import tomli_w
import typer
from r3a_logger.logger import (  # type: ignore[import-untyped]
    get_current_logger,
    initialize_logging,
)
from rich.console import Console
from rich.panel import Panel

from browser_launcher.browsers.factory import BrowserFactory
from browser_launcher.config import BrowserLauncherConfig
from browser_launcher.cookies import (
    CookieConfig,
    _dump_cookies_from_browser,
    inject_and_verify_cookies,
    read_cookies_from_browser,
)
from browser_launcher.screenshot import IDGenerator, _capture_screenshot
from browser_launcher.utils import get_command_context

app = typer.Typer(help="Browser launcher CLI tool")
console = Console()


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
    """Cache cookies from the browser session for the specified user/env."""
    try:
        target_cookies = list(cookie_config_data["users"][user][env]["cookies"].keys())
        target_domains = list(
            {
                val["domain"]
                for val in cookie_config_data["users"][user][env]["cookies"].values()
            }
        )
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
                    cookie_config_data["users"][user][env]["cookies"][cookie["name"]][
                        "domain"
                    ],
                    cookie["name"],
                    cookie.get("value", ""),
                )
            # Save config back to file

            config_file = get_home_directory() / "config.toml"
            if cookie_config:
                with open(config_file, "wb") as f:
                    tomli_w.dump(cookie_config.config_data, f)
            console.print(
                f"✅ Cached {len(target_browser_cookies)} cookies for "
                f"{user}/{env}/{target_domains}"
            )
            logger.info(
                f"Saved {len(target_browser_cookies)} cookies "
                f"for {user}/{env}/{target_domains}"
            )
            if cookie_config:
                users_json = json.dumps(cookie_config.config_data["users"], indent=2)
                logger.debug(f"Cookies: {users_json}")
        else:
            console.print(f"⚠️ No cookies found for domain {domain}")
            logger.debug(f"⚠️ No cookies found for domain {domain}")
    except Exception as e:
        console.print(f"❌ Error caching cookies: {e}")
        logger.error(f"Error caching cookies: {e}", exc_info=True)


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

    # Load cookie config and inject cached cookies if available
    try:
        cookie_config_data = config_loader.config_data
        cookie_config = CookieConfig(cookie_config_data)
        logger.info(
            f"Attempting to inject cookies for domain {domain} (user={user}, env={env})"
        )

        injected_cookies = inject_and_verify_cookies(
            browser_controller, user, env, cookie_config
        )

        if injected_cookies:
            console.print(
                f"✅ Injected {len(injected_cookies)} cookies: "
                f"{[cookie['name'] for cookie in injected_cookies]}"
            )

            if url:
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
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
    except (AttributeError, termios.error, OSError):
        # If we can't set terminal mode (e.g., in tests or non-TTY), continue anyway
        pass

    try:
        console.print("Press Ctrl+D or q to exit.")
        console.print("Press 'Enter' to capture a screenshot.")
        console.print("Press 's' to save/cache cookies for this session.")
        console.print("Press 'c' to dump all cookies from the browser.")

        while True:
            if browser_controller.driver.session_id is None:
                console.print(
                    "session has gone bad, you need to relaunch to be able to "
                    "capture screenshot"
                )
            char = sys.stdin.read(1)
            if not char or char == "\x04" or char.lower() == "q":  # EOF or Ctrl+D
                # Exit the loop
                break
            elif char.lower() == "\n" or char.lower() == "\r":
                # Capture screenshot
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
                # Save/cache cookies for this session
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
                # Dump all cookies from the browser
                _dump_cookies_from_browser(browser_controller.driver, logger, console)

    except EOFError:
        console.print("\nExiting...")
    finally:
        # Restore original terminal settings if they were saved
        if old_settings is not None:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except (termios.error, OSError):
                pass
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
