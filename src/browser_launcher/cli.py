"""CLI interface for browser_launcher using Typer."""

import sys
from pathlib import Path
from typing import Optional
from importlib import resources

import typer
from rich.console import Console
from rich.panel import Panel

from .logger import get_command_context, initialize_logging, get_current_logger

app = typer.Typer(help="Browser launcher CLI tool")
console = Console()


def get_home_directory() -> Path:
    """Get the home directory path."""
    return Path.home() / ".browser_launcher"


def get_log_directory() -> Path:
    """Get the log directory path."""
    return get_home_directory() / "logs"


def create_config_template() -> str:
    """Create the content for the initial configuration file by reading from assets/default_config.toml."""
    with resources.files("browser_launcher").joinpath("assets/default_config.toml").open("rb") as f:
        return f.read().decode("utf-8")


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force reinitialize even if directory exists"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"),
    debug: bool = typer.Option(False, "--debug", help="Enable comprehensive debugging logs (DEBUG level, includes verbose)")
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

    # Initialize logging first
    initialize_logging(verbose=verbose, debug=debug)
    logger = get_current_logger()
    if logger is None:
        raise RuntimeError("Logger was not initialized correctly.")
    
    # Log command execution
    context = get_command_context("init", {"force": force, "verbose": verbose, "debug": debug})
    logger.info(f"Starting browser launcher initialization - {context}")
    
    
    if home_dir_exists and not force:
        logger.warning(f"Browser launcher directory already exists: {home_dir}")
        console.print(f"📁 [yellow]Browser launcher directory already exists:[/yellow] {home_dir}")
        console.print("[yellow]Use --force to reinitialize[/yellow]")
        return
    
    try:
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
            border_style="green"
        )
        console.print(panel)
        
        # Log successful completion
        logger.info(f"Browser launcher initialization completed successfully")
        
    except PermissionError:
        error_msg = f"Permission denied: Cannot create directory {home_dir}"
        logger.error(error_msg)
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        console.print("💡 Try running with appropriate permissions or check directory access")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Failed to initialize: {e}"
        logger.error(error_msg, exc_info=True)
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        sys.exit(1)


@app.command()
def launch(
    url: Optional[str] = typer.Argument(None, help="URL to open"),
    browser: Optional[str] = typer.Option(None, "--browser", help="Browser to use"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"),
    debug: bool = typer.Option(False, "--debug", help="Enable comprehensive debugging logs (DEBUG level, includes verbose)")
):
    """Launch a browser with specified options.
    
    Logging Behavior:
    - Default: Clean console output, file logging only
    - --verbose: INFO level console logging for operational details
    - --debug: DEBUG level console logging including internal execution flow
    - File logging: Always active regardless of console flags
    """
    # Initialize logging first
    initialize_logging(verbose=verbose, debug=debug)
    logger = get_current_logger()
    if logger is None:
        raise RuntimeError("Logger was not initialized correctly.")
    
    # Log command execution
    context = get_command_context("launch", {
        "url": url, "browser": browser, "headless": headless,
        "verbose": verbose, "debug": debug
    })
    logger.info(f"Starting browser launch - {context}")
    
    # Load configuration
    from browser_launcher.config import BrowserLauncherConfig
    from browser_launcher.browsers.factory import BrowserFactory
    
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
        browser_config = config_loader.get_browser_config(selected_browser, headless=headless)
    except Exception as e:
        console.print(f"❌ [red]Error loading browser config:[/red] {e}")
        logger.error(f"Error loading browser config: {e}")
        sys.exit(1)
    
    # Instantiate browser launcher
    try:
        bl = BrowserFactory.create(selected_browser, browser_config, logger)
    except Exception as e:
        console.print(f"❌ [red]Error instantiating browser:[/red] {e}")
        logger.error(f"Error instantiating browser: {e}")
        sys.exit(1)
    
    # Validate binary
    
    # Determine URL
    launch_url = url or config_loader.get_default_url()
    console.print(f"🚀 Launching {selected_browser} at {launch_url}")
    logger.info(f"Launching {selected_browser} at {launch_url}")
    
    # Launch browser
    try:
        bl.launch(url=launch_url)
    except Exception as e:
        console.print(f"❌ [red]Error launching browser:[/red] {e}")
        logger.error(f"Error launching browser: {e}")
        sys.exit(1)
    
    try:
        console.print("Press Ctrl+D (or Ctrl+Z on Windows) to exit.")
        while True:
            if bl.driver.session_id is None:
                console.print("session has gone bad, you need to relaunch to be able to capture screenshot")
            char = sys.stdin.read(1)
            if not char:
                break
    except EOFError:
        console.print("\nExiting...")
    finally:
        try:
            bl.driver.close()
        except Exception:
            pass


@app.command()
def clean(
    force: bool = typer.Option(False, "--force", help="Force cleanup without confirmation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed operational logs (INFO level)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    debug: bool = typer.Option(False, "--debug", help="Enable comprehensive debugging logs (DEBUG level, includes verbose)")
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
    context = get_command_context("clean", {
        "force": force, "verbose": verbose, "yes": yes, "debug": debug
    })

    if verbose:
        console.print(f"Starting browser launcher cleanup : {context}")

    if not home_dir_exists:
        console.print(f"📁 [yellow]Browser launcher directory does not exist:[/yellow] {home_dir}")
        console.print("💡 Nothing to clean up")
        return

    # Show what will be deleted
    if verbose:
        console.print(f"📂 Directory contents to be removed:")
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
            default=False
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
            border_style="red"
        )
        console.print(panel)
        
        # Log successful completion
        console.print(f"Browser launcher cleanup completed successfully")
        
    except PermissionError:
        error_msg = f"Permission denied: Cannot remove directory {home_dir}"
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        console.print("💡 Try running with appropriate permissions or check directory access")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Failed to clean up: {e}"
        console.print(f"❌ [red]Error:[/red] {error_msg}")
        sys.exit(1)


if __name__ == "__main__":
    app()