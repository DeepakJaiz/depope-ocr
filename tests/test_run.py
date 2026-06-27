from importlib import import_module


def test_run_imports():
    mod = import_module("run")
    assert mod.__name__ == "run"
