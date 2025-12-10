from browser_launcher import launch, __version__


def test_launch_prints(capsys):
    launch()
    captured = capsys.readouterr()
    assert "Launching browser (placeholder)" in captured.out


def test_version():
    assert __version__ == "0.1.0"
