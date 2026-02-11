from typer.testing import CliRunner

from browser_launcher.cli import app


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


def test_clean_verbose_with_extra_folder(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    extra_folder = home_dir / "extra_folder"
    extra_folder.mkdir()
    (extra_folder / "extra_file.txt").write_text("extra")
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--yes", "--verbose"])
    assert "Starting browser launcher cleanup" in result.output
    assert "dummy.txt" in result.output
    assert "extra_folder" in result.output
    assert "extra_file.txt" in result.output
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


def test_clean_permission_error(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    # Simulate PermissionError in shutil.rmtree
    monkeypatch.setattr(
        "shutil.rmtree",
        lambda path: (_ for _ in ()).throw(PermissionError("Mock permission error")),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--force"])
    assert "Permission denied" in result.output
    assert "Error:" in result.output
    assert result.exit_code != 0


def test_clean_general_exception(tmp_path, monkeypatch):
    home_dir = setup_temp_home(tmp_path)
    monkeypatch.setattr("browser_launcher.cli.get_home_directory", lambda: home_dir)
    # Simulate generic Exception in shutil.rmtree
    monkeypatch.setattr(
        "shutil.rmtree",
        lambda path: (_ for _ in ()).throw(Exception("Mock general error")),
    )
    runner = CliRunner()
    result = runner.invoke(app, ["clean", "--force"])
    assert "Failed to clean up" in result.output
    assert "Error:" in result.output
    assert result.exit_code != 0
