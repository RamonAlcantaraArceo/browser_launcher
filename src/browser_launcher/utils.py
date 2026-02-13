"""Utility functions for browser_launcher."""

from typing import Optional


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
