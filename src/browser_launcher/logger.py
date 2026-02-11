"""Logging utilities for browser_launcher."""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Global logger instance for CLI and other modules
_logger: Optional[logging.Logger] = None
_instance: Any = None


class BrowserLauncherLogger:
    """Custom logger for browser_launcher with file and console logging."""

    def __init__(
        self,
        log_dir: Path,
        log_level: str = "INFO",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_logging: bool = True,
    ):
        """Initialize the logger.

        Args:
            log_dir: Directory to store log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            max_file_size: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            console_logging: Whether to enable console logging
        """
        self.log_dir = log_dir
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_logging = console_logging

        # Create logs directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger("browser_launcher")
        self.logger.setLevel(self.log_level)

        # Clear any existing handlers
        self.logger.handlers.clear()

        # Create formatters
        self.file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        self.console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(funcName)s | %(message)s",
            datefmt="%H:%M:%S",
        )

        # Setup file logging with rotation
        log_file = self.log_dir / "browser_launcher.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(file_handler)

        # Setup console logging if enabled
        if self.console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self.console_formatter)
            self.logger.addHandler(console_handler)

    def set_level(self, log_level: str) -> None:
        """Change the logging level.

        Args:
            log_level: New logging level (DEBUG, INFO, WARNING, ERROR)
        """
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)

    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance.

        Returns:
            The logger instance
        """
        return self.logger

    def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up log files older than specified days.

        Args:
            days: Number of days to keep log files
        """
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                self.logger.info(f"Cleaned up old log file: {log_file.name}")


def get_logger(
    log_dir: Path, log_level: str = "INFO", console_logging: bool = True
) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_logging: Whether to enable console logging

    Returns:
        Configured logger instance
    """
    # Use a global instance to avoid multiple handlers
    global _instance
    if _instance is None:
        _instance = BrowserLauncherLogger(
            log_dir=log_dir, log_level=log_level, console_logging=console_logging
        )

    return _instance.get_logger()


def setup_logging(
    log_dir: Path, log_level: str = "INFO", console_logging: bool = True
) -> logging.Logger:
    """Setup and configure logging for browser_launcher.

    Args:
        log_dir: Directory for log files
        log_level: Logging level
        console_logging: Whether to enable console logging

    Returns:
        Configured logger instance
    """
    # Clear any existing global instance
    global _instance
    _instance = None

    return get_logger(log_dir, log_level, console_logging)


def initialize_logging(
    verbose: bool = False, debug: bool = False, console_logging: bool = False
) -> None:
    """Initialize logging based on verbosity settings.
    Args:
        verbose: Enable verbose logging (INFO level)
        debug: Enable debug logging (DEBUG level)
        console_logging: Enable console logging (default False)
    """
    global _logger
    # Determine log level
    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"

    log_dir = Path.home() / ".browser_launcher" / "logs"
    _logger = setup_logging(
        log_dir=log_dir, log_level=log_level, console_logging=console_logging
    )
    # NOTE:
    # - Use `logger` (from logger module) for all debug/info/warning/error logs.
    # - Use `typer.echo` and `console.print` for user-facing output only.
    # - Do NOT use `logging.getLogger` or the default Python logger directly in CLI.
    # - Logging and user output are strictly separated in all commands.
    if debug:
        _logger.debug("Logging initialized at DEBUG level")
    elif verbose:
        _logger.info("Logging initialized at INFO level")
    else:
        _logger.info("Logging initialized at WARNING level (file logging only)")


def get_current_logger():
    """Get the current logger instance."""
    global _logger
    if _logger is None:
        initialize_logging()
    return _logger


def get_command_context(command: str, args: Optional[dict] = None) -> str:
    """Generate a context string for logging.

    Args:
        command: The command being executed
        args: Optional dictionary of command arguments

    Returns:
        Formatted context string
    """
    if args:
        # Filter out None values and format arguments
        filtered_args = {k: v for k, v in args.items() if v is not None}
        if filtered_args:
            args_str = " | ".join(f"{k}={v}" for k, v in filtered_args.items())
            return f"[{command}] {args_str}"

    return f"[{command}]"
