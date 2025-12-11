"""CLI interface for browser_launcher using Typer."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Browser launcher CLI tool")
console = Console()


def get_home_directory() -> Path:
    """Get the home directory path."""
    return Path.home() / ".browser_launcher"


def create_config_template() -> str:
    """Create the content for the initial configuration file."""
    return """# Browser Launcher Configuration
# This file contains settings for the browser launcher

[general]
# Default browser to use (chrome, firefox, safari, edge)
default_browser = "chrome"

# Default timeout for browser operations (in seconds)
timeout = 30

[urls]
# Default URLs to open
homepage = "https://www.google.com"

[browsers]
# Browser-specific settings
[chrome]
binary_path = ""
headless = false

[firefox]
binary_path = ""
headless = false

[safari]
binary_path = ""
headless = false

[edge]
binary_path = ""
headless = false
"""


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Force reinitialize even if directory exists"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """Initialize browser launcher by creating configuration directory and files."""
    home_dir = get_home_directory()
    
    if home_dir.exists() and not force:
        console.print(f"📁 [yellow]Browser launcher directory already exists:[/yellow] {home_dir}")
        console.print("[yellow]Use --force to reinitialize[/yellow]")
        return
    
    try:
        # Create directory
        if verbose:
            console.print(f"📁 Creating directory: {home_dir}")
        
        home_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config file
        config_file = home_dir / "config.toml"
        if verbose:
            console.print(f"📝 Creating config file: {config_file}")
        
        config_content = create_config_template()
        config_file.write_text(config_content)
        
        # Create logs directory
        logs_dir = home_dir / "logs"
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
        
    except PermissionError:
        console.print(f"❌ [red]Permission denied:[/red] Cannot create directory {home_dir}")
        console.print("💡 Try running with appropriate permissions or check directory access")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Error:[/red] Failed to initialize: {e}")
        sys.exit(1)


@app.command()
def launch(
    url: Optional[str] = typer.Argument(None, help="URL to open"),
    browser: Optional[str] = typer.Option(None, "--browser", help="Browser to use"),
    headless: bool = typer.Option(False, "--headless", help="Run browser in headless mode")
):
    """Launch a browser with specified options."""
    console.print("🚀 Browser launcher functionality")
    console.print(f"URL: {url or 'Not specified'}")
    console.print(f"Browser: {browser or 'Default'}")
    console.print(f"Headless: {headless}")
    
    # TODO: Implement actual browser launching logic
    console.print("💡 This is a placeholder - actual browser launching to be implemented")


@app.command()
def clean(
    force: bool = typer.Option(False, "--force", help="Force cleanup without confirmation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """Clean up browser launcher by removing configuration directory and files."""
    home_dir = get_home_directory()
    
    if not home_dir.exists():
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
        
    except PermissionError:
        console.print(f"❌ [red]Permission denied:[/red] Cannot remove directory {home_dir}")
        console.print("💡 Try running with appropriate permissions or check directory access")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ [red]Error:[/red] Failed to clean up: {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()