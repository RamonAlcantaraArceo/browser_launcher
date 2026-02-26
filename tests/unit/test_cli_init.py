import tempfile
import unittest.mock
from pathlib import Path

import pytest
from typer.testing import CliRunner

from browser_launcher import __version__
from browser_launcher.cli import create_config_template, get_home_directory


@pytest.mark.unit
def test_get_home_directory():
    """Test that get_home_directory returns the correct path."""
    home_dir = get_home_directory()
    expected = Path.home() / ".browser_launcher"
    assert home_dir == expected


@pytest.mark.unit
def test_get_console_logging_setting_true_false(monkeypatch):
    # Patch config reading to return True and False for console_logging
    from browser_launcher import cli
    from browser_launcher.config import BrowserLauncherConfig

    # Patch constructor with desired config_data
    def mock_init_false_console(self, config_path=None):
        self.config_data = {"logging": {"console_logging": False}}

    
    def mock_init_true_console(self, config_path=None):
        self.config_data = {"logging": {"console_logging": True}}
    
    monkeypatch.setattr(BrowserLauncherConfig, "__init__", mock_init_false_console)

    assert cli.get_console_logging_setting() is False

    monkeypatch.setattr(BrowserLauncherConfig, "__init__", mock_init_true_console)
    assert cli.get_console_logging_setting() is True


@pytest.mark.unit
def test_create_config_template():
    """Test that config template is created correctly."""
    config_content = create_config_template()
    assert "# Browser Launcher Configuration" in config_content
    assert "[general]" in config_content
    assert "default_browser" in config_content
    assert "timeout" in config_content
    assert "[browsers]" in config_content


@pytest.mark.unit
def test_init_creates_directory_and_files():
    """Test that init command creates directory and config file."""
    import importlib
    import shutil

    with tempfile.TemporaryDirectory() as temp_dir:
        real_asset = (
            Path(__file__).parent.parent.parent
            / "src"
            / "browser_launcher"
            / "assets"
            / "default_config.toml"
        )
        assert real_asset.exists(), f"Asset file missing: {real_asset}"
        asset_content = real_asset.read_text()
        with (
            unittest.mock.patch("browser_launcher.cli.Path.home") as mock_home,
            unittest.mock.patch(
                "browser_launcher.cli.create_config_template",
                return_value=asset_content,
            ),
        ):
            mock_home.return_value = Path(temp_dir)
            # Ensure .browser_launcher does not exist before running CLI
            home_dir = Path(temp_dir) / ".browser_launcher"
            if home_dir.exists():
                shutil.rmtree(home_dir)
            import browser_launcher.cli

            importlib.reload(browser_launcher.cli)
            from browser_launcher.cli import app

            runner = CliRunner()
            result = runner.invoke(app, ["init", "--verbose"])
            assert result.exit_code == 0
            assert home_dir.exists() and home_dir.is_dir()
            config_file = home_dir / "config.toml"
            assert config_file.exists() and config_file.is_file()
            logs_dir = home_dir / "logs"
            assert logs_dir.exists() and logs_dir.is_dir()


@pytest.mark.unit
def test_init_skips_existing_directory():
    """Test that init command skips when directory already exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch("browser_launcher.cli.Path.home") as mock_home:
            mock_home.return_value = Path(temp_dir)

            from typer.testing import CliRunner

            from browser_launcher.cli import app

            runner = CliRunner()

            # First run - should create the directory
            result1 = runner.invoke(app, ["init"])
            assert result1.exit_code == 0

            # Second run - should skip
            result2 = runner.invoke(app, ["init"])
            assert result2.exit_code == 0
            assert "already exists" in result2.output


@pytest.mark.unit
def test_init_permission_error(monkeypatch):
    import tempfile
    import unittest.mock

    from typer.testing import CliRunner

    from browser_launcher.cli import app

    with tempfile.TemporaryDirectory() as temp_dir:
        home_dir = Path(temp_dir) / ".browser_launcher"
        monkeypatch.setattr("browser_launcher.cli.Path.home", lambda: Path(temp_dir))
        # Patch Path.mkdir to raise only for home_dir
        real_mkdir = Path.mkdir

        def permission_side_effect(self, *args, **kwargs):
            if self == home_dir:
                raise PermissionError("Mock permission error")
            return real_mkdir(self, *args, **kwargs)

        with unittest.mock.patch("pathlib.Path.mkdir", new=permission_side_effect):
            runner = CliRunner()
            result = runner.invoke(app, ["init", "--force"])
            assert result.exit_code != 0
            assert "Permission denied" in result.output
            assert "Error:" in result.output


@pytest.mark.unit
def test_init_general_exception(monkeypatch):
    import tempfile
    import unittest.mock

    from typer.testing import CliRunner

    from browser_launcher.cli import app

    with tempfile.TemporaryDirectory() as temp_dir:
        home_dir = Path(temp_dir) / ".browser_launcher"
        monkeypatch.setattr("browser_launcher.cli.Path.home", lambda: Path(temp_dir))
        # Patch Path.mkdir to raise only for home_dir
        real_mkdir = Path.mkdir

        def general_side_effect(self, *args, **kwargs):
            if self == home_dir:
                raise Exception("Mock general error")
            return real_mkdir(self, *args, **kwargs)

        with unittest.mock.patch("pathlib.Path.mkdir", new=general_side_effect):
            runner = CliRunner()
            result = runner.invoke(app, ["init", "--force"])
            assert result.exit_code != 0
            assert "Failed to initialize" in result.output
            assert "Error:" in result.output


@pytest.mark.unit
def test_version():
    """Test that version is correctly defined."""
    assert __version__ == "0.1.0"


@pytest.mark.unit
def test_clean_removes_directory_and_files():
    """Test that clean command removes directory and all its contents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch("browser_launcher.cli.Path.home") as mock_home:
            mock_home.return_value = Path(temp_dir)

            from typer.testing import CliRunner

            from browser_launcher.cli import app

            runner = CliRunner()

            # First create the directory
            result1 = runner.invoke(app, ["init"])
            assert result1.exit_code == 0

            # Verify directory exists
            home_dir = Path(temp_dir) / ".browser_launcher"
            assert home_dir.exists()

            # Now clean it (with force flag to skip confirmation)
            result2 = runner.invoke(app, ["clean", "--force"])
            assert result2.exit_code == 0

            # Verify directory is removed
            assert not home_dir.exists()


@pytest.mark.unit
def test_clean_handles_nonexistent_directory():
    """Test that clean command handles non-existent directory gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch("browser_launcher.cli.Path.home") as mock_home:
            mock_home.return_value = Path(temp_dir)
            from typer.testing import CliRunner

            from browser_launcher.cli import app

            runner = CliRunner()
            result = runner.invoke(app, ["clean", "--force"])
            assert result.exit_code == 0
            output = result.output
            # Should mention directory does not exist and nothing to clean up
            assert "does not exist" in output
            assert "Nothing to clean up" in output


@pytest.mark.unit
def test_init_runtime_error_logger(monkeypatch):
    import tempfile
    import unittest.mock

    from typer.testing import CliRunner

    from browser_launcher.cli import app

    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr("browser_launcher.cli.Path.home", lambda: Path(temp_dir))
        # Patch get_current_logger to return None to trigger RuntimeError
        with unittest.mock.patch(
            "browser_launcher.cli.get_current_logger", return_value=None
        ):
            runner = CliRunner()
            result = runner.invoke(app, ["init", "--force"])
            assert result.exit_code == 1
            assert "Logger was not initialized correctly." in result.output
