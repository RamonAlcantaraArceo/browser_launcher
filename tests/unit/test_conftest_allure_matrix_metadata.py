"""Unit tests for matrix-aware Allure metadata fixtures in tests.conftest."""

from __future__ import annotations

import importlib
import inspect

import pytest


def _invoke_fixture(module, fixture_name: str, request=None):
    fixture_obj = getattr(module, fixture_name)
    fixture_fn = getattr(fixture_obj, "__wrapped__", fixture_obj)
    params = inspect.signature(fixture_fn).parameters
    if params:
        return fixture_fn(request)
    return fixture_fn()


class _FakeDynamic:
    def __init__(self):
        self.parameter_calls = []
        self.sub_suite_calls = []

    def parameter(self, *args, **kwargs):
        self.parameter_calls.append((args, kwargs))

    def sub_suite(self, *args, **kwargs):
        self.sub_suite_calls.append((args, kwargs))


class _FakeAllure:
    def __init__(self):
        self.dynamic = _FakeDynamic()


@pytest.mark.unit
def test_allure_python_version_metadata_fixture_exists():
    module = importlib.import_module("conftest")
    assert hasattr(module, "allure_python_version_metadata")


@pytest.mark.unit
def test_allure_python_version_metadata_applies_parameter_and_sub_suite(monkeypatch):
    module = importlib.import_module("conftest")
    fake_allure = _FakeAllure()

    monkeypatch.setenv("ALLURE_PYTHON_VERSION", "3.11")
    monkeypatch.setattr(module, "HAS_ALLURE", True)
    monkeypatch.setattr(module, "allure", fake_allure)

    _invoke_fixture(module, "allure_python_version_metadata")

    assert fake_allure.dynamic.parameter_calls == [
        (("python_version", "Python 3.11"), {})
    ]
    assert fake_allure.dynamic.sub_suite_calls == [(("Python 3.11",), {})]


@pytest.mark.unit
def test_allure_python_version_metadata_noops_without_allure(monkeypatch):
    module = importlib.import_module("conftest")
    fake_allure = _FakeAllure()

    monkeypatch.setenv("ALLURE_PYTHON_VERSION", "3.12")
    monkeypatch.setattr(module, "HAS_ALLURE", False)
    monkeypatch.setattr(module, "allure", fake_allure)

    _invoke_fixture(module, "allure_python_version_metadata")

    assert fake_allure.dynamic.parameter_calls == []
    assert fake_allure.dynamic.sub_suite_calls == []
