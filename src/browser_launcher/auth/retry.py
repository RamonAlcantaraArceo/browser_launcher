"""Interactive retry system for authentication."""

import logging
import time
from typing import Any, Dict

import typer
from rich.console import Console

from browser_launcher.auth.config import AuthConfig


class AuthRetryHandler:
    """Manages retry attempts for authentication with interactive user prompts.

    Handles retry logic, credential updates, delay between attempts, and
    user-friendly error messages via Rich console.
    """

    def __init__(
        self,
        config: AuthConfig,
        console: Console,
        logger: logging.Logger,
    ):
        """Initialize AuthRetryHandler.

        Args:
            config: Authentication configuration with retry settings.
            console: Rich console for user-facing messages.
            logger: Logger instance for retry events.
        """
        self.config = config
        self.console = console
        self.logger = logger
        self.current_attempt = 0

    def should_retry(
        self,
        error_message: str,
        apply_delay: bool = True,
    ) -> bool:
        """Check if another retry attempt should be made.

        Prompts the user for a retry decision if max attempts have not been reached.
        Applies retry delay if configured and requested.

        Args:
            error_message: The error message from the failed attempt.
            apply_delay: Whether to apply the configured retry delay.

        Returns:
            True if the user wants to retry, False otherwise.
        """
        total_attempts = self.config.retry_attempts + 1

        if self.current_attempt >= total_attempts:
            self.logger.warning(
                f"Max retry attempts ({total_attempts}) reached, cannot retry"
            )
            return False

        # Display error message with attempt info
        self.display_error_message(
            error_message,
            attempt=self.current_attempt,
            total=total_attempts,
        )

        # Prompt user for retry decision
        remaining = self.get_remaining_attempts()
        retry = typer.confirm(
            f"Retry authentication with updated credentials? "
            f"({remaining} attempts remaining)",
            default=True,
        )

        if not retry:
            self.logger.info("User declined to retry authentication")
            return False

        # Apply delay if requested and configured
        if apply_delay and self.config.retry_delay_seconds > 0:
            self.logger.debug(
                f"Applying retry delay of {self.config.retry_delay_seconds}s"
            )
            time.sleep(self.config.retry_delay_seconds)

        return True

    def prompt_for_credentials(self) -> Dict[str, Any]:
        """Prompt user for updated credential values.

        Prompts for each credential in the config, hiding input for
        password/token fields.

        Returns:
            Dictionary of updated credentials.
        """
        if not self.config.credentials:
            self.logger.debug("No credentials configured, skipping prompt")
            return {}

        self.console.print("\n[yellow]Please provide updated credentials:[/yellow]")

        updated_credentials = dict(self.config.credentials)
        for key, value in self.config.credentials.items():
            hide_input = "password" in key.lower() or "token" in key.lower()
            default_value = None if hide_input else str(value)

            updated_credentials[key] = typer.prompt(
                f"Enter {key}",
                default=default_value,
                hide_input=hide_input,
            )

        self.logger.debug(f"Prompted for {len(updated_credentials)} credential fields")
        return updated_credentials

    def increment_attempt(self) -> None:
        """Increment the current attempt counter."""
        self.current_attempt += 1
        self.logger.debug(f"Incremented attempt to {self.current_attempt}")

    def get_remaining_attempts(self) -> int:
        """Get the number of remaining retry attempts.

        Returns:
            Number of attempts remaining (including current attempt).
        """
        total_attempts = self.config.retry_attempts + 1
        remaining = total_attempts - self.current_attempt
        return max(0, remaining)

    def display_error_message(
        self,
        message: str,
        attempt: int,
        total: int,
    ) -> None:
        """Display error message with Rich formatting.

        Args:
            message: The error message to display.
            attempt: The current attempt number.
            total: The total number of attempts allowed.
        """
        self.console.print(
            f"\n[red]❌ Authentication failed (attempt {attempt}/{total}):[/red] "
            f"{message}\n"
        )
        self.logger.warning(
            f"Authentication failed on attempt {attempt}/{total}: {message}"
        )
