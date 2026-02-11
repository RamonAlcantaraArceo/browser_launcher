"""Unit tests for logger.py (BrowserLauncherLogger and helpers)."""

import logging
import tempfile
from pathlib import Path
import shutil
import os
import pytest
from browser_launcher.logger import (
    BrowserLauncherLogger, get_logger, setup_logging, get_current_logger, get_command_context
)

def test_logger_creates_log_file_and_console(tmp_path):
    log_dir = tmp_path / "logs"
    logger_obj = BrowserLauncherLogger(log_dir, log_level="DEBUG", console_logging=True)
    logger = logger_obj.get_logger()
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warn message")
    logger.error("error message")
    log_file = log_dir / "browser_launcher.log"
    assert log_file.exists()
    with open(log_file) as f:
        content = f.read()
        assert "debug message" in content
        assert "info message" in content
        assert "warn message" in content
        assert "error message" in content


def test_logger_respects_log_level(tmp_path):
    log_dir = tmp_path / "logs"
    logger_obj = BrowserLauncherLogger(log_dir, log_level="WARNING", console_logging=False)
    logger = logger_obj.get_logger()
    logger.debug("should not appear")
    logger.info("should not appear")
    logger.warning("should appear")
    logger.error("should appear")
    log_file = log_dir / "browser_launcher.log"
    with open(log_file) as f:
        content = f.read()
        assert "should not appear" not in content
        assert "should appear" in content


def test_set_level_changes_log_level(tmp_path):
    log_dir = tmp_path / "logs"
    logger_obj = BrowserLauncherLogger(log_dir, log_level="ERROR", console_logging=False)
    logger = logger_obj.get_logger()
    logger_obj.set_level("DEBUG")
    logger.debug("debug now visible")
    log_file = log_dir / "browser_launcher.log"
    with open(log_file) as f:
        content = f.read()
        assert "debug now visible" in content


def test_cleanup_old_logs(tmp_path):
    log_dir = tmp_path / "logs"
    logger_obj = BrowserLauncherLogger(log_dir, log_level="INFO", console_logging=False)
    # Create a fake old log file
    old_log = log_dir / "old.log"
    old_log.write_text("old log")
    # Set mtime to 40 days ago
    old_time = (os.path.getmtime(old_log) - (40 * 24 * 60 * 60))
    os.utime(old_log, (old_time, old_time))
    logger_obj.cleanup_old_logs(days=30)
    assert not old_log.exists()


def test_get_logger_and_setup_logging(tmp_path):
    log_dir = tmp_path / "logs"
    logger1 = get_logger(log_dir, log_level="INFO", console_logging=False)
    logger2 = get_logger(log_dir, log_level="DEBUG", console_logging=False)
    assert logger1 is logger2  # Should be singleton
    logger3 = setup_logging(log_dir, log_level="DEBUG", console_logging=False)
    assert logger3 is not None
    assert logger3 is get_logger(log_dir, log_level="DEBUG", console_logging=False)


def test_get_command_context():
    ctx = get_command_context("launch", {"browser": "chrome", "headless": True, "foo": None})
    assert ctx == "[launch] browser=chrome | headless=True"
    ctx2 = get_command_context("init")
    assert ctx2 == "[init]"


def test_get_current_logger_returns_logger(monkeypatch, tmp_path):
    # Patch Path.home to tmp_path for isolation
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Remove global _logger if set
    from browser_launcher import logger as logger_mod
    logger_mod._logger = None
    log = get_current_logger()
    assert isinstance(log, logging.Logger)
