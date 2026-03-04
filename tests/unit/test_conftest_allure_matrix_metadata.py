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
        self.parent_suite_calls = []
        self.suite_calls = []
        self.sub_suite_calls = []

    def parameter(self, *args, **kwargs):
        self.parameter_calls.append((args, kwargs))

    def parent_suite(self, *args, **kwargs):
        self.parent_suite_calls.append((args, kwargs))

    def suite(self, *args, **kwargs):
        self.suite_calls.append((args, kwargs))

    def sub_suite(self, *args, **kwargs):
        self.sub_suite_calls.append((args, kwargs))


class _FakeAllure:
    def __init__(self):
        self.dynamic = _FakeDynamic()


class _FakeModule:
    def __init__(self, name="tests.unit.test_auth_config"):
        self.__name__ = name


class _FakeNode:
    def __init__(self, module=None, fspath=None):
        self.module = module or _FakeModule()
        if fspath is not None:
            self.fspath = fspath


class _FakeRequest:
    def __init__(self, node=None):
        self.node = node or _FakeNode()


@pytest.mark.unit
def test_allure_python_version_metadata_fixture_exists():
    module = importlib.import_module("conftest")
    assert hasattr(module, "allure_python_version_metadata")


@pytest.mark.unit
def test_allure_python_version_metadata_applies_hierarchy_and_parameter(monkeypatch):
    module = importlib.import_module("conftest")
    fake_allure = _FakeAllure()
    # Use a fresh module and node for this test
    test_module = _FakeModule()
    node = _FakeNode(module=test_module)
    fake_request = _FakeRequest(node=node)

    monkeypatch.setenv("ALLURE_PYTHON_VERSION", "3.11")
    monkeypatch.setattr(module, "allure", fake_allure)

    _invoke_fixture(module, "allure_python_version_metadata", request=fake_request)

    assert fake_allure.dynamic.parameter_calls == [
        (("python_version", "Python 3.11"), {})
    ]
    assert fake_allure.dynamic.parent_suite_calls == [(("tests.misc",), {})]
    assert fake_allure.dynamic.suite_calls == [(("Python 3.11",), {})]
    assert fake_allure.dynamic.sub_suite_calls == [(("test_auth_config",), {})]


@pytest.mark.unit
def test_allure_python_version_metadata_smoke_path(monkeypatch):
    module = importlib.import_module("conftest")
    fake_allure = _FakeAllure()

    # Simulate a smoke test path
    class FakeFspath:
        def __str__(self):
            return "tests/smoke/test_auth_integration.py"

        @property
        def parts(self):
            return ("tests", "smoke", "test_auth_integration.py")

    # Use a fresh module and node for this test
    test_module = _FakeModule(name="tests.smoke.test_auth_integration")
    node = _FakeNode(module=test_module, fspath=FakeFspath())
    fake_request = _FakeRequest(node=node)

    monkeypatch.setenv("ALLURE_PYTHON_VERSION", "3.14")
    monkeypatch.setattr(module, "allure", fake_allure)

    _invoke_fixture(module, "allure_python_version_metadata", request=fake_request)

    assert fake_allure.dynamic.parameter_calls == [
        (("python_version", "Python 3.14"), {})
    ]
    assert fake_allure.dynamic.parent_suite_calls == [(("tests.smoke",), {})]
    assert fake_allure.dynamic.suite_calls == [(("Python 3.14",), {})]
    assert fake_allure.dynamic.sub_suite_calls == [(("test_auth_integration",), {})]
