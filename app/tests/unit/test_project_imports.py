import importlib


def test_core_packages_import() -> None:
    modules = [
        "app",
        "app.ui",
        "app.data_pipeline",
        "app.analysis",
        "app.domain",
    ]

    for module_name in modules:
        assert importlib.import_module(module_name)
