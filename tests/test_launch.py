from browser_launcher import __version__
from browser_launcher.cli import get_home_directory, create_config_template
import tempfile
from pathlib import Path
import unittest.mock
from typer.testing import CliRunner


def test_get_home_directory():
    """Test that get_home_directory returns the correct path."""
    home_dir = get_home_directory()
    expected = Path.home() / ".browser_launcher"
    assert home_dir == expected


def test_create_config_template():
    """Test that config template is created correctly."""
    config_content = create_config_template()
    assert "# Browser Launcher Configuration" in config_content
    assert "[general]" in config_content
    assert "default_browser" in config_content
    assert "timeout" in config_content
    assert "[browsers]" in config_content


def test_init_creates_directory_and_files():
    """Test that init command creates directory and config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the home directory to use our temp directory
        with unittest.mock.patch('browser_launcher.cli.Path.home') as mock_home:
            mock_home.return_value = Path(temp_dir)
            
            from browser_launcher.cli import app
            
            runner = CliRunner()
            result = runner.invoke(app, ['init', '--verbose'])
            
            # Check that command executed successfully
            assert result.exit_code == 0
            
            # Check that directory was created
            home_dir = Path(temp_dir) / ".browser_launcher"
            assert home_dir.exists()
            assert home_dir.is_dir()
            
            # Check that config file was created
            config_file = home_dir / "config.toml"
            assert config_file.exists()
            assert config_file.is_file()
            
            # Check that logs directory was created
            logs_dir = home_dir / "logs"
            assert logs_dir.exists()
            assert logs_dir.is_dir()


def test_init_skips_existing_directory():
    """Test that init command skips when directory already exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch('browser_launcher.cli.Path.home') as mock_home:
            mock_home.return_value = Path(temp_dir)
            
            from browser_launcher.cli import app
            from typer.testing import CliRunner
            
            runner = CliRunner()
            
            # First run - should create the directory
            result1 = runner.invoke(app, ['init'])
            assert result1.exit_code == 0
            
            # Second run - should skip
            result2 = runner.invoke(app, ['init'])
            assert result2.exit_code == 0
            assert "already exists" in result2.output


def test_version():
    """Test that version is correctly defined."""
    assert __version__ == "0.1.0"


def test_clean_removes_directory_and_files():
    """Test that clean command removes directory and all its contents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch('browser_launcher.cli.Path.home') as mock_home:
            mock_home.return_value = Path(temp_dir)
            
            from browser_launcher.cli import app
            from typer.testing import CliRunner
            
            runner = CliRunner()
            
            # First create the directory
            result1 = runner.invoke(app, ['init'])
            assert result1.exit_code == 0
            
            # Verify directory exists
            home_dir = Path(temp_dir) / ".browser_launcher"
            assert home_dir.exists()
            
            # Now clean it (with force flag to skip confirmation)
            result2 = runner.invoke(app, ['clean', '--force'])
            assert result2.exit_code == 0
            
            # Verify directory is removed
            assert not home_dir.exists()


def test_clean_handles_nonexistent_directory():
    """Test that clean command handles non-existent directory gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with unittest.mock.patch('browser_launcher.cli.Path.home') as mock_home:
            mock_home.return_value = Path(temp_dir)
            
            from browser_launcher.cli import app
            from typer.testing import CliRunner
            
            runner = CliRunner()
            result = runner.invoke(app, ['clean', '--force'])
            
            # Should exit successfully but indicate nothing to clean
            assert result.exit_code == 0
            assert "does not exist" in result.output
            assert "Nothing to clean up" in result.output
