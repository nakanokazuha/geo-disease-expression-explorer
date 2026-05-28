import ast
from pathlib import Path

FORBIDDEN_IMPORT_ROOTS = (
    "app.data_pipeline",
    "app.analysis.differential_expression",
)


def _module_name_from_path(path: Path) -> str:
    return ".".join(path.with_suffix("").parts)


def _is_forbidden_import(module_name: str) -> bool:
    return any(
        module_name == forbidden_root or module_name.startswith(f"{forbidden_root}.")
        for forbidden_root in FORBIDDEN_IMPORT_ROOTS
    )


def _resolve_import_from_module(path: Path, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module

    package_parts = _module_name_from_path(path).split(".")[:-1]
    parent_count = node.level - 1
    if parent_count > len(package_parts):
        return None

    resolved_parts = package_parts[: len(package_parts) - parent_count]
    if node.module is not None:
        resolved_parts.extend(node.module.split("."))

    return ".".join(resolved_parts) if resolved_parts else None


def _assert_no_forbidden_imports(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_import_from_module(path, node)
            if module_name is not None:
                imported_modules.append(module_name)
                imported_modules.extend(
                    f"{module_name}.{alias.name}" for alias in node.names
                )

    forbidden_imports = [
        module_name
        for module_name in imported_modules
        if _is_forbidden_import(module_name)
    ]

    assert not forbidden_imports, (
        f"{path} imports forbidden modules: {', '.join(forbidden_imports)}"
    )


def test_streamlit_entrypoint_exists() -> None:
    assert Path("app/ui/app.py").exists()


def test_resolve_import_from_module_handles_relative_forbidden_imports() -> None:
    app_node = ast.parse("from ..data_pipeline import jobs").body[0]
    view_node = ast.parse("from ...analysis import differential_expression").body[0]

    assert isinstance(app_node, ast.ImportFrom)
    assert isinstance(view_node, ast.ImportFrom)
    assert _resolve_import_from_module(Path("app/ui/app.py"), app_node) == (
        "app.data_pipeline"
    )
    assert _resolve_import_from_module(
        Path("app/ui/views/dashboard_overview.py"),
        view_node,
    ) == "app.analysis"
    assert _is_forbidden_import("app.data_pipeline.jobs")
    assert _is_forbidden_import("app.analysis.differential_expression")


def test_streamlit_entrypoint_stays_thin() -> None:
    _assert_no_forbidden_imports(Path("app/ui/app.py"))


def test_ui_modules_do_not_import_pipeline_or_heavy_analysis() -> None:
    ui_module_paths = sorted(Path("app/ui").rglob("*.py"))

    for ui_module_path in ui_module_paths:
        _assert_no_forbidden_imports(ui_module_path)


def test_ui_import_boundary_scan_includes_visualization_views() -> None:
    ui_module_paths = sorted(Path("app/ui").rglob("*.py"))

    assert Path("app/ui/views/volcano_plot.py") in ui_module_paths
    assert Path("app/ui/views/heatmap_view.py") in ui_module_paths


def test_entrypoint_handles_missing_gold_artifact(monkeypatch) -> None:
    import app.ui.app as ui_app

    source = Path("app/ui/app.py").read_text(encoding="utf-8")
    calls: list[tuple[str, tuple[object, ...]]] = []

    def record_call(name: str):
        def recorder(*args: object, **_kwargs: object) -> None:
            calls.append((name, args))

        return recorder

    def raise_missing_gold() -> object:
        raise ui_app.GoldArtifactNotFoundError("missing")

    def fail_dashboard_render(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("dashboard renderers must not be called")

    monkeypatch.setattr(ui_app, "load_gold_bundle", raise_missing_gold)
    monkeypatch.setattr(ui_app.st, "set_page_config", record_call("set_page_config"))
    monkeypatch.setattr(ui_app.st, "title", record_call("title"))
    monkeypatch.setattr(ui_app.st, "caption", record_call("caption"))
    monkeypatch.setattr(ui_app.st, "warning", record_call("warning"))
    monkeypatch.setattr(ui_app.st, "info", record_call("info"))
    monkeypatch.setattr(ui_app.st, "code", record_call("code"))
    monkeypatch.setattr(ui_app, "render_dashboard_overview", fail_dashboard_render)
    monkeypatch.setattr(
        ui_app,
        "render_dashboard_interactions",
        fail_dashboard_render,
    )

    ui_app.main()

    assert "GoldArtifactNotFoundError" in source
    assert "run_full_refresh" not in source
    assert ("warning", ("No published Gold artifact bundle is available yet.",)) in calls
    assert any(name == "info" for name, _args in calls)
    assert ("code", ("missing",)) in calls


def test_entrypoint_renders_dashboard_interactions() -> None:
    source = Path("app/ui/app.py").read_text(encoding="utf-8")

    assert "render_dashboard_interactions" in source
    assert "run_full_refresh" not in source
