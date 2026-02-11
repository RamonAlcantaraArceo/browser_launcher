import pytest
from typer.testing import CliRunner
from browser_launcher.cli import app
from pathlib import Path
import shutil

def setup_temp_home(tmp_path):
    home_dir = tmp_path / ".browser_launcher"
    home_dir.mkdir()
    (home_dir / "dummy.txt").write_text("test")
    return home_dir

def test_clean_verbose_output(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--yes", "--verbose"])
    assert "Starting browser launcher cleanup" in result.output
    assert "dummy.txt" in result.output
    assert "Removing directory" in result.output
    assert "Cleanup Complete" in result.output

def test_clean_force_skips_confirmation(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--force"])
    assert "Cleanup Complete" in result.output
    assert "Are you sure" not in result.output

def test_clean_without_force_prompts(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    runner = CliRunner()
    result = runner.invoke(app, ["clean"], input="n\n")
    assert "Are you sure" in result.output
    assert "Cleanup cancelled" in result.output

def test_clean_handles_nonexistent_directory_verbose(tmp_path, monkeypatch):
    home_dir = tmp_path / ".browser_launcher"
    # Do not create the directory
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--force", "--verbose"])
    assert "does not exist" in result.output
    assert "Nothing to clean up" in result.output
