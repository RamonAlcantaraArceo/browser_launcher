"""Firefox browser launcher implementation."""

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BrowserConfig, BrowserLauncher


class FirefoxLauncher(BrowserLauncher):
    """Firefox browser launcher implementation.

    Firefox uses different flag syntax than Chrome:
    - Uses single dash flags like -headless instead of --headless
    - Profile management with -profile flag instead of --user-data-dir
    - Limited experimental options compared to Chrome
    """

    def __init__(self, config: BrowserConfig) -> None:
        """Initialize Firefox launcher with configuration.

        Args:
            config: BrowserConfig instance with Firefox-specific settings
        """
        self.config = config

    @property
    def browser_name(self) -> str:
        """Return the browser name identifier.

        Returns:
            "firefox"
        """
        return "firefox"

    def validate_binary(self) -> None:
        """Validate that Firefox binary exists and is executable.

        Raises:
            FileNotFoundError: If binary path doesn't exist
            PermissionError: If binary is not executable
        """
        binary_path = Path(self.config.binary_path)

        if not binary_path.exists():
            raise FileNotFoundError(
                f"Firefox binary not found at {self.config.binary_path}"
            )

        if not binary_path.is_file():
            raise FileNotFoundError(
                f"Firefox binary path is not a file: {self.config.binary_path}"
            )

        if not (binary_path.stat().st_mode & 0o111):
            raise PermissionError(
                f"Firefox binary is not executable: {self.config.binary_path}"
            )

    def build_command_args(self) -> List[str]:
        """Build command line arguments for Firefox.

        Firefox uses different flag syntax:
        - -headless (instead of --headless)
        - -profile <path> (instead of --user-data-dir)

        Returns:
            List of command arguments starting with binary path
        """
        args: List[str] = [str(self.config.binary_path)]

        # Add headless flag if requested
        if self.config.headless:
            args.append("-headless")

        # Add profile path if user_data_dir is specified
        if self.config.user_data_dir:
            args.append("-profile")
            args.append(str(self.config.user_data_dir))

        # Add custom flags
        if self.config.custom_flags:
            args.extend(self.config.custom_flags)

        # Add extra options if provided (dict-based options)
        # For future extensions like preferences, app args, etc.
        if self.config.extra_options:
            # Extra options handling for Firefox can be extended here
            # For now, we store them but don't actively use them in args
            # They could be used for:
            # - Preference settings
            # - Environment variables
            # - Configuration files
            pass

        return args

    def launch(self) -> subprocess.Popen:  # type: ignore
        """Launch Firefox browser process.

        Validates the binary exists, builds command arguments, and spawns the
        Firefox process using subprocess.Popen.

        Returns:
            subprocess.Popen instance for the Firefox process

        Raises:
            FileNotFoundError: If Firefox binary doesn't exist
            PermissionError: If Firefox binary is not executable
        """
        self.validate_binary()
        args = self.build_command_args()
        return subprocess.Popen(args)
