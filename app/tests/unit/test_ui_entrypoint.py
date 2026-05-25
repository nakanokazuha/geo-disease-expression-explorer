from pathlib import Path


def test_streamlit_entrypoint_exists() -> None:
    entrypoint = Path("app/ui/app.py")

    assert entrypoint.exists()


def test_streamlit_entrypoint_stays_thin() -> None:
    source = Path("app/ui/app.py").read_text(encoding="utf-8")

    forbidden_imports = [
        "app.data_pipeline.ingestion",
        "app.data_pipeline.bronze",
        "app.data_pipeline.silver",
        "app.analysis.differential_expression",
    ]

    for forbidden_import in forbidden_imports:
        assert forbidden_import not in source
